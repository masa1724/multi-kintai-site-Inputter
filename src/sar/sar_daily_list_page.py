from datetime import datetime

from playwright.sync_api import Locator, Page, expect

from sar.sar_base_page import SarBasePage
from sar.sar_daily_edit_page import SarDailyEditPage


class SarDailyListPage(SarBasePage):
    """SAR 日報一覧画面のページオブジェクト。"""

    def __init__(self, page: Page):
        super().__init__(page)

    def open(self) -> "SarDailyListPage":
        """日報一覧画面を開く。"""
        expect(self.page.locator("#kinmu_date_search0")).to_be_visible(timeout=10000)
        return self

    def go_to_daily_edit(self, target_date: datetime) -> SarDailyEditPage:
        """日報一覧で指定日を検索し、日付リンクから日報編集画面を開く。"""
        target_date_str = self._format_date(target_date)
        daily_link = self._get_daily_link(target_date_str, False)
        if daily_link is None:
            raise RuntimeError(
                f"SAR 日報一覧の日付リンクが見つかりませんでした: {target_date_str}"
            )

        daily_link.click()
        self.wait_for_footer()
        self._open_edit_mode_if_needed()
        print(f"[INFO] SAR {target_date_str} の日報編集画面を開きました。")
        return SarDailyEditPage(self.page)

    def has_daily_link(self, target_date: datetime) -> bool:
        """指定日の行に日付リンクが存在するか確認する。"""
        return self._get_daily_link(self._format_date(target_date), True) is not None

    def createEmptyDailyRecord(self, target_date: datetime) -> SarDailyEditPage:
        """日付だけ入れた空の日報レコードを新規作成する。"""
        target_date_str = self._format_date(target_date)
        print(f"[INFO] SAR 日報を新規作成します: {target_date_str}")

        create_button = self.page.get_by_role("button", name="新規作成")
        if create_button.count() == 0:
            create_button = self.page.locator("input[type='button'][value='新規作成']")
        if create_button.count() == 0:
            raise RuntimeError("SAR 日報一覧の新規作成ボタンが見つかりませんでした")

        create_button.first.click()
        self.wait_for_footer()

        kinmu_date = self.page.locator("#kinmu_date")
        expect(kinmu_date).to_be_visible(timeout=10000)
        kinmu_date.fill(target_date_str)

        save_button = self.page.get_by_role("button", name="保存")
        if save_button.count() == 0:
            save_button = self.page.locator("input[type='submit'][value='保存']")
        if save_button.count() == 0:
            save_button = self.page.locator("input[type='button'][value='保存']")
        if save_button.count() == 0:
            raise RuntimeError("SAR 日報編集画面の保存ボタンが見つかりませんでした")

        self.page.once("dialog", lambda dialog: dialog.accept())
        save_button.first.click()
        self.wait_for_footer()

        print(f"[INFO] SAR {target_date_str} の空日報を作成しました。")
        return SarDailyEditPage(self.page)

    def _get_daily_link(self, target_date: str, search: bool) -> Locator | None:
        if search:
            self._search_by_date(target_date)

        row = self._get_row_by_date(target_date)
        if row is None:
            return None

        kinmu_status = self._get_cell_text_by_header(row, "勤務S")
        print(f"[INFO] SAR 日報一覧 勤務S: {target_date}={kinmu_status}")

        if kinmu_status == "月締済":
            message = f"[ERROR] SAR 日報 {target_date} は月締済のため、変更できません。"
            print(message)
            raise RuntimeError(message)

        daily_link = row.locator(
            "a",
            has=self.page.locator(
                f"span[id^='kinmu_date'][id$='_VIEW_LABEL']:text-is('{target_date}')"
            ),
        )
        if daily_link.count() == 0:
            return None
        return daily_link.first

    def _search_by_date(self, target_date: str) -> None:
        self.open()
        print(f"[INFO] SAR 日報一覧で対象日を検索します: {target_date}")

        search0 = self.page.locator("#kinmu_date_search0")
        search0.fill(target_date)
        search1 = self.page.locator("#kinmu_date_search1")
        search1.fill(target_date)
        search1.press("Enter")
        self.wait_for_footer()

    def _format_date(self, target_date: datetime) -> str:
        return target_date.strftime("%Y/%m/%d")

    def _back_to_daily_list(self) -> None:
        if self.page.locator("#kinmu_date_search0").count() > 0:
            return

        back_link = self.page.locator("a").filter(has_text="一覧に戻る")
        if back_link.count() > 0:
            back_link.first.click()
            self.wait_for_footer()
            return

        self.click_header_menu("name1")

    def _get_row_by_date(self, target_date: str) -> Locator | None:
        date_input = self.page.locator(
            f"input[id^='kinmu_date'][name='form.kinmu_date'][value='{target_date}']"
        )
        if date_input.count() > 0:
            return date_input.first.locator("xpath=ancestor::tr[1]")

        date_label = self.page.locator(
            f"span[id^='kinmu_date'][id$='_VIEW_LABEL']:text-is('{target_date}')"
        )
        if date_label.count() > 0:
            return date_label.first.locator("xpath=ancestor::tr[1]")

        return None

    def _get_cell_text_by_header(self, row: Locator, header_text: str) -> str:
        header_index = self._get_header_index(row, header_text)
        if header_index is None:
            return ""

        cell = row.locator("td").nth(header_index)
        if cell.count() == 0:
            return ""

        return cell.inner_text().strip()

    def _get_header_index(self, row: Locator, header_text: str) -> int | None:
        table = row.locator("xpath=ancestor::table[1]")
        headers = table.locator("th")
        for index in range(headers.count()):
            if headers.nth(index).inner_text().strip() == header_text:
                return index
        return None

    def _open_edit_mode_if_needed(self) -> None:
        work_start_hour = self.page.locator("#shukkin_time_hour")
        if work_start_hour.count() > 0 and work_start_hour.first.is_visible():
            return

        edit_targets = (
            self.page.get_by_role("button", name="変更"),
            self.page.locator("input[type='button'][value='変更']"),
            self.page.locator("input[type='submit'][value='変更']"),
            self.page.locator("a").filter(has_text="変更"),
        )
        for edit_target in edit_targets:
            if edit_target.count() > 0 and edit_target.first.is_visible():
                self.page.once("dialog", lambda dialog: dialog.accept())
                edit_target.first.click()
                self.wait_for_footer()
                return
