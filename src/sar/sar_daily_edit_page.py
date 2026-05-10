from typing import TYPE_CHECKING

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from sar.sar_base_page import SarBasePage
from work_segment import SarWorkArea

if TYPE_CHECKING:
    from sar.sar_daily_record import SarDailyRecord


class SarDailyEditPage(SarBasePage):
    """SAR 日報編集画面のページオブジェクト。"""

    def __init__(self, page: Page):
        super().__init__(page)

    def input_daily_fields(self, daily_info: "SarDailyRecord"):
        """日付以外の日報入力項目を編集画面へ反映する。"""
        print(
            f"[INFO] SAR 日報フォーム入力を開始します: {daily_info.target_date.strftime('%Y-%m-%d')}"
        )

        # 勤務エリア
        self.select_work_area(daily_info.work_area)

        # 出勤時刻
        # 退勤時刻
        self.input_time(daily_info.start_time, daily_info.end_time)

        # 追加休憩時間
        additional_break_minutes = daily_info.calculate_additional_break_minutes()
        hours, minutes = divmod(additional_break_minutes, 60)
        self.input_additional_break(hours, minutes)

        # 勤務状況の備考
        self.input_notes(daily_info.notes)

        # 作業(H)残り の算出
        work_hour, work_minute = daily_info.calculate_work_result_time()

        # 作業実績一覧
        # 部門コード
        self.input_work_result_department(
            daily_info.work_result_department_code, prepare=True
        )
        # PJコード
        self.input_work_result_project(
            daily_info.work_result_project_code, prepare=False
        )
        # 工程コード
        self.input_work_result_process(daily_info.work_result_process, prepare=False)
        # 作業(H)残り
        self.input_work_result_time(work_hour, work_minute, prepare=False)
        # 備考
        self.input_work_result_notes(daily_info.work_result_notes, prepare=False)

        if daily_info.notes is not None:
            self.input_notes(daily_info.notes)

        print("[INFO] SAR 日報フォーム入力が完了しました")
        return self

    def select_work_area(self, area: SarWorkArea):
        """勤務エリアを選択する。"""
        print(f"[INFO] SAR 勤務エリアを選択します: {area.jp_name} ({area.value})")

        self.page.locator("#kinmu_area").select_option(area.value)
        return self

    def input_time(self, start: str, end: str):
        """通常の勤務開始・終了時刻を入力する。"""
        print(f"[INFO] SAR 勤務時間を入力します: {start} - {end}")
        start_hour, start_min = self._split_time(start)
        end_hour, end_min = self._split_time(end)

        self.page.locator("#shukkin_time_hour").select_option(start_hour)
        self.page.locator("#shukkin_time_min").select_option(start_min)
        self.page.locator("#taikin_time_hour").select_option(end_hour)
        self.page.locator("#taikin_time_min").select_option(end_min)

        return self

    def input_additional_break(self, hour: str | int, minute: str | int):
        """追加休憩の時・分を直接入力する。"""
        print(f"[INFO] SAR 追加休憩を入力します: {hour}:{minute}")
        self.page.locator("#tsuika_kyuukei_time_hour").select_option(str(int(hour)))
        self.page.locator("#tsuika_kyuukei_time_min").select_option(str(int(minute)))
        return self

    def input_notes(self, text: str):
        """日報全体の備考を入力する。"""
        print(f"[INFO] SAR 日報備考を入力します:\n{text}")
        if text is None:
            return self

        note = self.page.locator("#bikou")
        if note.count() > 0:
            note.fill(text)

        return self

    def input_work_result_department(self, department_code: str, prepare: bool = True):
        """作業実績の部門を選択する。"""
        if department_code is None:
            return self
        print(f"[INFO] SAR 作業実績の部門を選択します: {department_code}")
        if prepare:
            self._ensure_work_result_row()
        self._input_first_available(
            (
                "#sagyou_jisseki_view_bumon_name_view0",
                "[id^='sagyou_jisseki_view_bumon_name_view']",
                "[name='form.bumon_name']",
            ),
            department_code,
        )
        return self

    def input_work_result_project(self, project_code: str, prepare: bool = True):
        """作業実績の PJ を選択する。"""
        if project_code is None:
            return self
        print(f"[INFO] SAR 作業実績の PJ を選択します: {project_code}")
        if prepare:
            self._ensure_work_result_row()
        self._input_first_available(
            (
                "#sagyou_jisseki_view_project_name_view0",
                "[id^='sagyou_jisseki_view_project_name_view']",
                "[name='form.project_name']",
            ),
            project_code,
        )
        return self

    def input_work_result_process(self, process: str, prepare: bool = True):
        """作業実績の工程を選択する。"""
        if process is None:
            return self
        print(f"[INFO] SAR 作業実績の工程を選択します: {process}")
        if prepare:
            self._ensure_work_result_row()
        self._input_first_available(
            (
                "#sagyou_jisseki_view_pj_koutei_view0",
                "[id^='sagyou_jisseki_view_pj_koutei_view']",
                "[name='form.pj_koutei']",
            ),
            process,
        )
        return self

    def input_work_result_time(
        self, hour: str | int, minute: str | int = 0, prepare: bool = True
    ):
        """作業実績の作業時間を入力する。"""
        print(f"[INFO] SAR 作業実績の作業時間を入力します: {hour}:{minute}")
        if prepare:
            self._ensure_work_result_row()

        self.page.locator("#sagyou_jisseki_view_sagyou_time_hour_view0").select_option(
            str(int(hour))
        )
        self.page.locator("#sagyou_jisseki_view_sagyou_time_min_view0").select_option(
            str(int(minute))
        )
        if self._input_first_available(
            (
                "#sagyou_jisseki_view_sagyou_time_hour_view0",
                "[id^='sagyou_jisseki_view_sagyou_time_hour_view']",
                "[name='form.sagyou_time_hour']",
            ),
            str(int(hour)),
        ):
            self._input_first_available(
                (
                    "#sagyou_jisseki_view_sagyou_time_min_view0",
                    "[id^='sagyou_jisseki_view_sagyou_time_min_view']",
                    "[name='form.sagyou_time_min']",
                ),
                str(int(minute)),
            )
        else:
            self._input_first_available(
                (
                    "#sagyou_jisseki_view_sagyou_time0",
                    "[id^='sagyou_jisseki_view_sagyou_time']",
                    "[name='form.sagyou_time']",
                ),
                self._format_work_result_time(hour, minute),
                required=True,
            )

        return self

    def input_work_result_notes(self, text: str, prepare: bool = True):
        """作業実績の備考を入力する。"""
        print(f"[INFO] SAR 作業実績の備考を入力します:\n{text}")
        if text is None:
            return self

        if prepare:
            self._prepare_work_result_editor()

        self._input_first_available(
            (
                "#sagyou_jisseki_view_text_bikou0",
                "#sagyou_jisseki_view_bikou0",
                "[id^='sagyou_jisseki_view_text_bikou']",
                "[id^='sagyou_jisseki_view_bikou']",
                "[name='form.bikou']",
            ),
            text,
            required=True,
        )

        return self

    def register(self):
        """編集内容を申請する。"""
        print("[INFO] SAR 申請ボタンをクリックします")
        self.page.once("dialog", lambda dialog: dialog.accept())
        self.page.get_by_role("button", name="登録").first.click()
        self.wait_for_footer()
        print("[INFO] SAR 申請処理が完了しました")
        return self

    def _prepare_work_result_editor(self) -> None:
        self._ensure_work_result_row()
        self._open_first_work_result_editor()

    def _ensure_work_result_row(self) -> None:
        if self._has_work_result_row():
            print("[INFO] SAR 作業実績行は既に存在するため追加しません。")
            return

        add_button = self.page.locator("#addLineBtn")
        if add_button.count() == 0:
            print("[WARN] SAR 作業実績行を作成する追加ボタンが見つかりません。")
            return

        print("[INFO] SAR 作業実績行を追加します。")
        add_button.first.click()
        self._wait_for_work_result_row()

    def _open_first_work_result_editor(self) -> None:
        edit_button = self.page.locator(".ichiran_01_mid_editbtn").first
        if edit_button.count() > 0:
            edit_button.click()

    def _split_time(self, value: str) -> tuple[str, str]:
        # 時刻文字列を「:」で分割して、時と分をゼロパディングなしの文字列で返す。例: "09:30" -> ("9", "30")
        hour, minute = value.split(":", maxsplit=1)
        return str(int(hour)), str(int(minute))

    def _time_to_minutes(self, value: str) -> int:
        hour, minute = self._split_time(value)
        return int(hour) * 60 + int(minute)

    def _format_work_result_time(self, hour: str | int, minute: str | int) -> str:
        total_minutes = int(hour) * 60 + int(minute)
        if total_minutes % 60 == 0:
            return str(total_minutes // 60)
        return f"{total_minutes / 60:.2f}".rstrip("0").rstrip(".")

    def _has_work_result_row(self) -> bool:
        work_result = self.page.locator("#sagyou_jisseki_view_dctp_recordset")
        return (
            work_result.locator("tr.ichiran_tr_data").count() > 0
            or work_result.locator("[id^='sagyou_jisseki_view_bumon_name']").count() > 0
            or work_result.locator(
                "[id^='sagyou_jisseki_view_bumon_name_view']"
            ).count()
            > 0
            or work_result.locator("[name='form.bumon_name']").count() > 0
        )

    def _wait_for_work_result_row(self) -> None:
        row = self.page.locator(
            "#sagyou_jisseki_view_dctp_recordset tr.ichiran_tr_data"
        ).first
        try:
            row.wait_for(state="attached", timeout=5000)
        except PlaywrightError:
            pass

    def _input_first_available(
        self,
        selectors: tuple[str, ...],
        value: str,
        required: bool = False,
    ) -> bool:
        for selector in selectors:
            locator = self.page.locator(selector)
            if locator.count() == 0:
                continue

            target = locator.first
            if self._try_select_option(target, value):
                return True
            if self._try_fill(target, value):
                return True

        if required:
            raise RuntimeError(
                f"SAR 作業実績の入力欄が見つかりませんでした: {', '.join(selectors)}"
            )
        return False

    def _try_select_option(self, locator, value: str) -> bool:
        try:
            locator.select_option(value)
            return True
        except PlaywrightError:
            return False

    def _try_fill(self, locator, value: str) -> bool:
        try:
            locator.fill(value)
            return True
        except PlaywrightError:
            return False
