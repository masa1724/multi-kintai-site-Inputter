import re
from datetime import datetime
from pathlib import Path

import yaml

from work_record import WorkRecord
from work_segment import HrmosWorkSegment


TIME_PATTERN = re.compile(r"^\d{1,2}:\d{2}$")
TIME_UNIT_MINUTES = 30


def load_input_records(yaml_path: str | Path) -> list[WorkRecord]:
    """
    YAML ファイルから勤怠入力レコード一覧を読み込む。

    読み込み後にバリデーションを実行し、不正な入力があれば ValueError を送出する。
    """
    path = Path(yaml_path)

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("YAML のルートはオブジェクト形式である必要があります。")

    raw_records = data.get("records")
    if not isinstance(raw_records, list):
        raise ValueError("YAML には records 配列が必要です。")

    records: list[WorkRecord] = []

    for index, raw in enumerate(raw_records, start=1):
        if not isinstance(raw, dict):
            raise ValueError(
                f"records[{index}] はオブジェクト形式である必要があります。"
            )

        try:
            record = WorkRecord(
                target_date=datetime.fromisoformat(str(raw["target_date"])),
                work_segment=HrmosWorkSegment[str(raw["work_segment"])],
                start_time=str(raw["start_time"]),
                end_time=str(raw["end_time"]),
                break1_start=_normalize_optional_str(raw.get("break1_start")),
                break1_end=_normalize_optional_str(raw.get("break1_end")),
                break2_start=_normalize_optional_str(raw.get("break2_start")),
                break2_end=_normalize_optional_str(raw.get("break2_end")),
                expense=_normalize_optional_str(raw.get("expense")),
                original_start=_normalize_optional_str(raw.get("original_start")),
                original_end=_normalize_optional_str(raw.get("original_end")),
                notes=_normalize_optional_str(raw.get("notes")),
                sar_work_result_department_code=_normalize_optional_str(
                    raw.get("sar_department_code")
                ),
                sar_work_result_project_code=_normalize_optional_str(
                    raw.get("sar_project_code")
                ),
                sar_work_result_process=_normalize_optional_str(raw.get("sar_process")),
                sar_work_result_notes=_normalize_optional_str(raw.get("sar_notes")),
            )
        except KeyError as e:
            raise ValueError(
                f"records[{index}] に必須項目がありません: {e.args[0]}"
            ) from e
        except Exception as e:
            raise ValueError(f"records[{index}] の読み込みに失敗しました: {e}") from e

        records.append(record)

    validate_input_records(records)

    return records


def validate_input_records(records: list[WorkRecord]) -> None:
    """
    入力レコード一覧の妥当性を検証する。

    エラーが1件でもあれば、すべてのエラー内容をまとめて ValueError として送出する。
    """
    all_errors: list[str] = []

    if len(records) == 0:
        all_errors.append("records は1件以上指定してください。")

    duplicate_dates = _find_duplicate_dates(records)
    for date_text in duplicate_dates:
        all_errors.append(f"target_date が重複しています: {date_text}")

    for index, record in enumerate(records, start=1):
        errors = _validate_record(record)
        for error in errors:
            all_errors.append(
                f"records[{index}] ({record.target_date.strftime('%Y-%m-%d')}): {error}"
            )

    if all_errors:
        joined = "\n".join(all_errors)
        raise ValueError(f"入力データにバリデーションエラーがあります。\n{joined}")


def _validate_record(record: WorkRecord) -> list[str]:
    """
    1件分の入力レコードを検証する。
    """
    errors: list[str] = []

    # 必須項目チェック
    if not record.start_time:
        errors.append("start_time は必須です。")

    if not record.end_time:
        errors.append("end_time は必須です。")

    # 時刻形式チェック
    for field_name, value in [
        ("start_time", record.start_time),
        ("end_time", record.end_time),
        ("break1_start", record.break1_start),
        ("break1_end", record.break1_end),
        ("break2_start", record.break2_start),
        ("break2_end", record.break2_end),
        ("original_start", record.original_start),
        ("original_end", record.original_end),
    ]:
        if value and not _is_valid_time_format(value):
            errors.append(f"{field_name} の形式が不正です（HH:mm）: {value}")
        elif value and not _is_time_unit(value):
            errors.append(f"{field_name} は30分単位で指定してください: {value}")

    # 勤務時間の前後関係チェック
    if _has_time_range(record.start_time, record.end_time):
        start_minutes = _to_minutes(record.start_time)
        end_minutes = _to_minutes(record.end_time)

        if start_minutes >= end_minutes:
            errors.append("start_time は end_time より前である必要があります。")

    # 休憩1の整合性チェック
    errors.extend(
        _validate_optional_time_range(
            label="break1",
            start_value=record.break1_start,
            end_value=record.break1_end,
            work_start=record.start_time,
            work_end=record.end_time,
        )
    )

    # 休憩2の整合性チェック
    errors.extend(
        _validate_optional_time_range(
            label="break2",
            start_value=record.break2_start,
            end_value=record.break2_end,
            work_start=record.start_time,
            work_end=record.end_time,
        )
    )

    # 自社勤務時間の整合性チェック
    errors.extend(
        _validate_optional_time_range(
            label="original",
            start_value=record.original_start,
            end_value=record.original_end,
            work_start=record.start_time,
            work_end=record.end_time,
        )
    )

    errors.extend(
        _validate_time_ranges_do_not_overlap(
            [
                ("break1", record.break1_start, record.break1_end),
                ("break2", record.break2_start, record.break2_end),
                ("original", record.original_start, record.original_end),
            ]
        )
    )

    # expense は数値のみ許可
    if record.expense and not record.expense.isdigit():
        errors.append("expense は数値で指定してください。")

    # 作業実績系は片方だけ指定されないように最低限チェック
    sar_fields = [
        record.sar_work_result_department_code,
        record.sar_work_result_project_code,
        record.sar_work_result_process,
    ]
    if any(sar_fields) and not all(sar_fields):
        errors.append(
            "sar_department_code / sar_project_code / sar_process は指定する場合すべて指定してください。"
        )

    return errors


def _validate_optional_time_range(
    label: str,
    start_value: str | None,
    end_value: str | None,
    work_start: str,
    work_end: str,
) -> list[str]:
    """
    任意の時間帯項目（休憩、自社勤務など）の整合性を検証する。
    """
    errors: list[str] = []

    # 開始と終了はセット必須
    if bool(start_value) != bool(end_value):
        errors.append(f"{label}_start / {label}_end はセットで指定してください。")
        return errors

    # どちらも未指定ならチェック不要
    if not start_value and not end_value:
        return errors

    # 形式エラーがある場合はここで打ち切る
    if not (_is_valid_time_format(start_value) and _is_valid_time_format(end_value)):
        return errors

    start_minutes = _to_minutes(start_value)
    end_minutes = _to_minutes(end_value)

    if start_minutes >= end_minutes:
        errors.append(f"{label}_start は {label}_end より前である必要があります。")
        return errors

    # 勤務時間が有効なときだけ勤務時間内チェックを行う
    if _has_time_range(work_start, work_end):
        work_start_minutes = _to_minutes(work_start)
        work_end_minutes = _to_minutes(work_end)

        if not (
            work_start_minutes <= start_minutes < work_end_minutes
            and work_start_minutes < end_minutes <= work_end_minutes
        ):
            errors.append(f"{label} は勤務時間内に収めてください。")

    return errors


def _normalize_optional_str(value: object) -> str:
    """
    任意文字列項目を正規化する。

    None や空文字、空白のみは空文字に変換する。
    """
    if value is None:
        return ""

    text = str(value).strip()
    return text if text else ""


def _is_valid_time_format(value: str) -> bool:
    """
    時刻文字列が HH:mm 形式として妥当かを判定する。
    """
    if not TIME_PATTERN.fullmatch(value):
        return False

    try:
        hour, minute = value.split(":", maxsplit=1)
        hour_num = int(hour)
        minute_num = int(minute)
    except ValueError:
        return False

    return 0 <= hour_num <= 23 and 0 <= minute_num <= 59


def _to_minutes(value: str) -> int:
    """
    HH:mm 形式の時刻を 0:00 起点の分に変換する。
    """
    hour, minute = value.split(":", maxsplit=1)
    return int(hour) * 60 + int(minute)


def _is_time_unit(value: str) -> bool:
    return _to_minutes(value) % TIME_UNIT_MINUTES == 0


def _has_time_range(start_value: str | None, end_value: str | None) -> bool:
    """
    開始・終了時刻がともに存在し、形式も妥当な場合に True を返す。
    """
    return (
        start_value is not None
        and end_value is not None
        and _is_valid_time_format(start_value)
        and _is_valid_time_format(end_value)
    )


def _time_ranges_overlap(start1: str, end1: str, start2: str, end2: str) -> bool:
    """
    2つの時間帯が重複しているかを判定する。
    """
    start1_minutes = _to_minutes(start1)
    end1_minutes = _to_minutes(end1)
    start2_minutes = _to_minutes(start2)
    end2_minutes = _to_minutes(end2)

    return not (end1_minutes <= start2_minutes or end2_minutes <= start1_minutes)


def _validate_time_ranges_do_not_overlap(
    ranges: list[tuple[str, str | None, str | None]],
) -> list[str]:
    errors: list[str] = []
    valid_ranges = [
        (label, start, end)
        for label, start, end in ranges
        if _has_time_range(start, end) and _to_minutes(start) < _to_minutes(end)
    ]

    for index, (label1, start1, end1) in enumerate(valid_ranges):
        for label2, start2, end2 in valid_ranges[index + 1 :]:
            if _time_ranges_overlap(start1, end1, start2, end2):
                errors.append(f"{label1} と {label2} が重複しています。")

    return errors


def _find_duplicate_dates(records: list[WorkRecord]) -> list[str]:
    """
    target_date の重複一覧を返す。
    """
    counts: dict[str, int] = {}

    for record in records:
        date_text = record.target_date.strftime("%Y-%m-%d")
        counts[date_text] = counts.get(date_text, 0) + 1

    return [date_text for date_text, count in counts.items() if count > 1]
