from dataclasses import dataclass
from datetime import datetime
from typing import TypeAlias

from work_segment import SarWorkArea
from utils import has_time_range
from work_record import WorkRecord

TimeRange: TypeAlias = tuple[str, str]
DEFAULT_LUNCH_BREAK: TimeRange = ("12:00", "13:00")
REGULAR_END_TIME = "18:00"


@dataclass
class SarDailyRecord:
    """1日分の SAR 勤怠入力値をまとめたデータ。"""

    # 出勤日
    target_date: datetime
    # 勤務エリア
    work_area: SarWorkArea
    # 出勤時刻（例: "09:00"）
    start_time: str
    # 退勤時刻（例: "18:00"）
    end_time: str
    # SARの追加休憩へ入力する休憩一覧。
    # 通常休憩の 12:00-13:00 は SAR 側の標準休憩として扱われるため含めない。
    additional_breaks: tuple[TimeRange, ...] = ()
    # 作業実績時間の計算に使う休憩一覧。
    # 通常休憩の 12:00-13:00 も含める。
    work_result_breaks: tuple[TimeRange, ...] = ()
    # 勤務状況の備考
    notes: str | None = None
    # 作業実績一覧の部門コード
    work_result_department_code: str | None = None
    # 作業実績一覧のPJコード
    work_result_project_code: str | None = None
    # 作業実績一覧の工程コード
    work_result_process: str | None = None
    # 作業実績一覧の備考
    work_result_notes: str | None = None

    def calculate_additional_break_minutes(self) -> int:
        """
        SAR の追加休憩へ入力する分数を計算する。

        additional_breaks に含まれる休憩時間を合算する。
        """
        return sum(
            _duration_minutes(start, end) for start, end in self.additional_breaks
        )

    def calculate_work_result_time(self) -> tuple[int, int]:
        """
        start_time / end_time / work_result_breaks から作業実績時間を算出する。

        戻り値は (時間, 30分単位の分) とする。
        例:
            7時間00分 -> (7, 0)
            7時間30分 -> (7, 30)
        """
        total_minutes = _duration_minutes(self.start_time, self.end_time)
        break_minutes = sum(
            _overlap_minutes(self.start_time, self.end_time, start, end)
            for start, end in self.work_result_breaks
        )
        work_minutes = max(total_minutes - break_minutes, 0)

        hours, minutes = divmod(work_minutes, 60)
        return hours, 5 if minutes >= 30 else 0


def convert_to_sar_daily_record(record: WorkRecord) -> SarDailyRecord:
    return SarDailyRecord(
        target_date=record.target_date,
        work_area=record.work_segment.sar_enum,
        start_time=record.start_time,
        end_time=_get_sar_end_time(record),
        additional_breaks=_get_sar_additional_breaks(record),
        work_result_breaks=_get_work_result_breaks(record),
        notes=_get_sar_work_result_notes(record),
        work_result_department_code=record.sar_work_result_department_code,
        work_result_project_code=record.sar_work_result_project_code,
        work_result_process=record.sar_work_result_process,
        work_result_notes=record.sar_work_result_notes,
    )


def _duration_minutes(start: str, end: str) -> int:
    minutes = _time_to_minutes(end) - _time_to_minutes(start)
    if minutes < 0:
        minutes += 24 * 60
    return minutes


def _overlap_minutes(
    start1: str,
    end1: str,
    start2: str,
    end2: str,
) -> int:
    start_minutes = max(_time_to_minutes(start1), _time_to_minutes(start2))
    end_minutes = min(_time_to_minutes(end1), _time_to_minutes(end2))
    return max(end_minutes - start_minutes, 0)


def _time_to_minutes(value: str) -> int:
    hour, minute = value.split(":", maxsplit=1)
    return int(hour) * 60 + int(minute)


def _get_sar_end_time(work_record: WorkRecord) -> str:
    if not _is_own_company_work_until_end(work_record):
        return work_record.end_time

    if (
        _has_hrmos_break(work_record, DEFAULT_LUNCH_BREAK)
        and work_record.original_start == DEFAULT_LUNCH_BREAK[1]
    ):
        return DEFAULT_LUNCH_BREAK[0]

    return work_record.original_start or work_record.end_time


def _is_own_company_work_until_end(work_record: WorkRecord) -> bool:
    return (
        has_time_range(work_record.original_start, work_record.original_end)
        and work_record.original_end == work_record.end_time
    )


def _has_hrmos_break(work_record: WorkRecord, time_range: TimeRange) -> bool:
    return time_range in (
        (work_record.break1_start, work_record.break1_end),
        (work_record.break2_start, work_record.break2_end),
    )


def _get_hrmos_breaks(work_record: WorkRecord) -> tuple[TimeRange, ...]:
    """
    HRMOS上の休憩一覧を返す。
    昼休み 12:00-13:00 も含む。
    """
    return tuple(
        (start, end)
        for start, end in (
            (work_record.break1_start, work_record.break1_end),
            (work_record.break2_start, work_record.break2_end),
        )
        if start and end
    )


def _get_sar_additional_breaks(
    work_record: WorkRecord,
) -> tuple[TimeRange, ...]:
    """
    SAR の追加休憩へ入力する休憩一覧を返す。
    昼休み 12:00-13:00 は除外する。
    """
    sar_breaks = tuple(
        time_range
        for time_range in _get_hrmos_breaks(work_record)
        if time_range != DEFAULT_LUNCH_BREAK
    )

    if has_time_range(
        work_record.original_start, work_record.original_end
    ) and not _is_own_company_work_until_end(work_record):
        sar_breaks = sar_breaks + (
            (work_record.original_start, work_record.original_end),
        )

    return sar_breaks


def _get_work_result_breaks(
    work_record: WorkRecord,
) -> tuple[TimeRange, ...]:
    """
    作業実績時間の計算に使う休憩一覧を返す。
    昼休み 12:00-13:00 も含める。
    自社の作業時間が勤務中に入る場合は、その時間帯も差し引く。
    """
    work_result_breaks = _get_hrmos_breaks(work_record)

    if has_time_range(
        work_record.original_start, work_record.original_end
    ) and not _is_own_company_work_until_end(work_record):
        work_result_breaks = work_result_breaks + (
            (work_record.original_start, work_record.original_end),
        )

    return work_result_breaks


def _get_sar_work_result_notes(work_record: WorkRecord) -> str:
    # SAR の作業実績備考には、自社の作業時間を「XXXのため、〇〇～△△は不在」の形式で記入する。
    if has_time_range(work_record.original_start, work_record.original_end):
        return (
            "自社作業のため、"
            f"{work_record.original_start}～{work_record.original_end}は不在"
        )

    if _time_to_minutes(work_record.end_time) < _time_to_minutes(REGULAR_END_TIME):
        return f"私用のため、{work_record.end_time}～{REGULAR_END_TIME}は不在"

    return ""
