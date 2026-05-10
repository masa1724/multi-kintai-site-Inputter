from typing import TYPE_CHECKING

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, expect
from work_segment import HrmosWorkSegment

if TYPE_CHECKING:
    from hrmos.hrmos_work_record import HrmosWorkRecord


class HrmosWorkEditPage:
    """HRMOS 勤怠編集画面のページオブジェクト。"""

    def __init__(self, page):
        self.page = page

    def input_work_fields(self, work_info: "HrmosWorkRecord"):
        """HRMOS の勤怠入力項目を編集画面へ反映する。"""
        print(
            f"[INFO] HRMOS 勤怠フォーム入力を開始します: {work_info.target_date.strftime('%Y-%m-%d')}"
        )

        self.input_time("", "")
        self.select_segment(work_info.segment)
        self.input_time(work_info.start_time, work_info.end_time)
        self.input_break1(work_info.break1_start, work_info.break1_end)
        self.input_break2(work_info.break2_start, work_info.break2_end)
        self.input_expense(work_info.expense)
        self.input_original_time(work_info.original_start, work_info.original_end)
        self.input_notes(work_info.notes)

        print("[INFO] HRMOS 勤怠フォーム入力が完了しました")
        return self

    def select_segment(self, segment: HrmosWorkSegment):
        """勤務区分を選択し、確認ダイアログが出た場合は承認する。"""
        print(f"[INFO] HRMOS 勤務区分を選択します: {segment.jp_name} ({segment.value})")

        self.page.locator("#work_segment_id").select_option(value=segment.value)

        yes_button = self.page.get_by_role("button", name="はい")
        try:
            print("[INFO] HRMOS 勤務区分変更の確認ダイアログを待機します（最大3秒）")
            yes_button.wait_for(state="visible", timeout=3000)

            print("[INFO] HRMOS 確認ダイアログが表示されたため「はい」をクリックします")
            yes_button.click()
        except PlaywrightTimeoutError:
            print("[INFO] HRMOS 確認ダイアログは表示されませんでした")

        return self

    def input_time(self, start: str, end: str):
        """通常の勤務開始・終了時刻を入力する。"""
        print(f"[INFO] HRMOS 勤務時間を入力します: {start} - {end}")

        self.page.locator("#work_start_at_str").fill(start)
        self.page.locator("#work_end_at_str").fill(end)

        return self

    def input_break1(self, start: str, end: str):
        """1つ目の休憩開始・終了時刻を入力する。"""
        print(f"[INFO] HRMOS 休憩時間1を入力します: {start} - {end}")

        self.page.locator("#work_break_1_start_at_str").fill(start)
        self.page.locator("#work_break_1_end_at_str").fill(end)

        return self

    def input_break2(self, start: str, end: str):
        """2つ目の休憩開始・終了時刻を入力する。"""
        print(f"[INFO] HRMOS 休憩時間2を入力します: {start} - {end}")

        self.page.locator("#work_break_2_start_at_str").fill(start)
        self.page.locator("#work_break_2_end_at_str").fill(end)

        return self

    def input_expense(self, value: str):
        """通勤交通費を入力する。在宅勤務など不要な日は 0 を渡す。"""
        print(f"[INFO] HRMOS 通勤交通費を入力します: {value}")

        self.page.locator("#work_expense").fill(value)

        return self

    def input_original_time(self, start: str, end: str):
        """会社独自項目の 自社の勤務時間を入力する。"""
        print(f"[INFO] HRMOS 自社の勤務時間を入力します: {start} - {end}")

        self.page.locator("#work_original_item_times_2_1_start_at_str").fill(start)
        self.page.locator("#work_original_item_times_2_1_end_at_str").fill(end)

        return self

    def input_notes(self, text: str):
        """備考欄を入力する。空文字を渡すと既存の内容をクリアする。"""
        print(f"[INFO] HRMOS 備考を入力します:\n{text}")

        self.page.locator("#work_notes").click()
        self.page.locator("#work_notes").fill(text)

        return self

    def apply(self):
        """編集内容を申請する。画面上に複数ある申請ボタンのうちフォーム側を押す。"""
        print("[INFO] HRMOS 申請ボタンをクリックします")

        self.page.locator("#work_notes").blur()
        self._click_apply_button()
        self._accept_apply_confirmation()
        self._wait_after_apply()

        print("[INFO] HRMOS 申請処理が完了しました")
        from hrmos.hrmos_works_page import HrmosWorksPage

        return HrmosWorksPage(self.page)

    def _click_apply_button(self) -> None:
        """勤怠フォーム内の申請ボタンを優先してクリックする。"""
        apply_button = self._find_apply_button()
        expect(apply_button).to_be_visible()
        expect(apply_button).to_be_enabled()

        apply_button.scroll_into_view_if_needed()
        dialog_handler = self._accept_browser_dialogs()
        try:
            apply_button.click()
        finally:
            self.page.remove_listener("dialog", dialog_handler)

    def _find_apply_button(self):
        form = self.page.locator("form", has=self.page.locator("#work_segment_id"))
        form_button = form.get_by_role("button", name="申請する")
        if form_button.count() > 0:
            return form_button.last

        apply_buttons = self.page.get_by_role("button", name="申請する")
        for index in range(apply_buttons.count() - 1, -1, -1):
            button = apply_buttons.nth(index)
            if button.is_visible():
                return button

        raise RuntimeError("[ERROR] HRMOS 申請ボタンが見つかりませんでした。")

    def _accept_browser_dialogs(self):
        def accept_dialog(dialog) -> None:
            print(f"[INFO] HRMOS ブラウザ確認ダイアログを承認します: {dialog.message}")
            dialog.accept()

        self.page.on("dialog", accept_dialog)
        return accept_dialog

    def _wait_after_apply(self) -> None:
        try:
            self.page.locator("#editGraphTable").wait_for(state="visible", timeout=5000)
            return
        except PlaywrightTimeoutError:
            pass

        if self.page.locator("#work_segment_id").count() > 0:
            messages = self._collect_error_messages()
            suffix = f" 画面上のメッセージ: {messages}" if messages else ""
            raise RuntimeError(
                "[ERROR] HRMOS 申請後も編集画面に残っています。"
                "申請ボタンのクリックまたは入力内容のエラー表示を確認してください。"
                f"{suffix}"
            )

        raise RuntimeError("[ERROR] HRMOS 申請後の画面を判定できませんでした。")

    def _accept_apply_confirmation(self) -> None:
        yes_button = self.page.get_by_role("button", name="はい")
        try:
            yes_button.wait_for(state="visible", timeout=3000)
        except PlaywrightTimeoutError:
            return

        print("[INFO] HRMOS 申請確認ダイアログで「はい」をクリックします")
        yes_button.click()

    def _collect_error_messages(self) -> str:
        selectors = (
            ".alert",
            ".alert-danger",
            ".error",
            ".errors",
            ".field_with_errors",
            "[class*='error']",
            "[class*='Error']",
        )
        messages: list[str] = []
        for selector in selectors:
            locator = self.page.locator(selector)
            for index in range(min(locator.count(), 5)):
                text = locator.nth(index).inner_text().strip()
                if text and text not in messages:
                    messages.append(text)

        return " / ".join(messages)
