from enum import StrEnum


class SarWorkArea(StrEnum):
    """SAR（Trustpro）の勤務エリア選択肢。"""

    OFFICE = ("通常勤務", "通常勤務")
    REMOTE = ("在宅勤務", "在宅勤務")
    SATELLITE = ("サテライト", "サテライト")
    OTHER = ("その他", "その他")
    NONE = ("", "-")

    def __new__(cls, value, jp_name):
        # SAR の実際の選択肢の値が分かり次第、この値を画面値に合わせる。
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.jp_name = jp_name
        return obj


class HrmosWorkSegment(StrEnum):
    """HRMOS の勤務区分 ID と画面表示名の対応表。"""

    OFFICE = ("1", "出勤", SarWorkArea.OFFICE)
    REMOTE = ("30", "出勤(在宅)", SarWorkArea.REMOTE)

    HOLIDAY = ("2", "公休", SarWorkArea.NONE)
    SUBSTITUTE = ("4", "振休", SarWorkArea.NONE)
    PAID_LEAVE = ("5", "有休", SarWorkArea.NONE)
    SPECIAL_LEAVE = ("10", "特休", SarWorkArea.NONE)
    ABSENCE = ("11", "欠勤", SarWorkArea.NONE)

    SUBSTITUTE_WORK = ("3", "振出(日曜以外)", SarWorkArea.REMOTE)
    SUBSTITUTE_WORK_SUN = ("60", "振出(日曜)", SarWorkArea.REMOTE)
    HALF_SUBSTITUTE_WORK = ("49", "半日振出(日曜以外)", SarWorkArea.REMOTE)
    HALF_SUBSTITUTE_WORK_SUN = ("61", "半日振出(日曜)", SarWorkArea.REMOTE)

    TRAINING = ("42", "終日研修", SarWorkArea.NONE)
    SUMMER_LEAVE = ("43", "夏季休暇", SarWorkArea.NONE)

    HALF_OFFICE_REMOTE = ("52", "半日出社+半日在宅", SarWorkArea.REMOTE)
    HALF_PAID_OFFICE = ("50", "半日有給+半日出社", SarWorkArea.OFFICE)
    HALF_PAID_REMOTE = ("51", "半日有給+半日在宅", SarWorkArea.REMOTE)
    HALF_SUBSTITUTE_OFFICE = ("53", "半日振休+半日出社", SarWorkArea.OFFICE)
    HALF_SUBSTITUTE_REMOTE = ("56", "半日振休+半日在宅", SarWorkArea.REMOTE)

    REMOTE_SUBSTITUTE = ("62", "在宅振出(日曜以外)", SarWorkArea.REMOTE)
    REMOTE_SUBSTITUTE_SUN = ("63", "在宅振出(日曜)", SarWorkArea.REMOTE)
    HALF_HOLIDAY_REMOTE_SUB = (
        "64",
        "半日公休+半日在宅振出(日曜以外)",
        SarWorkArea.REMOTE,
    )

    HALF_HOLIDAY_REMOTE_SUB_SUN = (
        "65",
        "半日公休+半日在宅振出(日曜)",
        SarWorkArea.REMOTE,
    )

    jp_name: str
    sar_enum: SarWorkArea

    def __new__(cls, value, jp_name, sar_enum):
        # 選択操作に渡す値は文字列 ID、ログには日本語名も出したいため属性に保持する。
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.jp_name = jp_name
        obj.sar_enum = sar_enum
        return obj
