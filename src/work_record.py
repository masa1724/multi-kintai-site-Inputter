from dataclasses import dataclass
from datetime import datetime

from work_segment import HrmosWorkSegment


@dataclass
class WorkRecord:
    """1日分の HRMOS 勤怠入力値をまとめたデータ。"""

    # 出勤日
    target_date: datetime
    # 勤務区分
    work_segment: HrmosWorkSegment
    # 出勤時刻（例: "09:00"）
    start_time: str
    # 退勤時刻（例: "18:00"）
    end_time: str
    # 休憩1 開始時刻（例: "12:00"）
    break1_start: str | None = None
    # 休憩1 終了時刻（例: "13:00"）
    break1_end: str | None = None
    # 休憩2 開始時刻（例: "19:00"）
    break2_start: str | None = None
    # 休憩2 終了時刻（例: "19:30"）
    break2_end: str | None = None
    # 通勤交通費用
    expense: str | None = None
    # 自社勤務 開始時刻
    original_start: str | None = None
    # 自社勤務 終了時刻
    original_end: str | None = None
    # 備考
    notes: str | None = None
    # SAR 作業実績一覧の部門コード
    sar_work_result_department_code: str | None = None
    # SAR 作業実績一覧のPJコード
    sar_work_result_project_code: str | None = None
    # SAR 作業実績一覧の工程コード
    sar_work_result_process: str | None = None
    # SAR 作業実績一覧の備考
    sar_work_result_notes: str | None = None
