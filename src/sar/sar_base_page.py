from playwright.sync_api import Page

# if TYPE_CHECKING:
#     from bk.sar_monthly_list_page import SarMonthlyListPage


class SarBasePage:
    """SAR ログイン後の共通ヘッダーのページオブジェクト。"""

    def __init__(self, page: Page):
        self.page = page

    #     def go_monthly_list(self) -> "SarMonthlyListPage":
    #         """SAR ヘッダーメニューから月報一覧画面を開く。"""
    #         from bk.sar_monthly_list_page import SarMonthlyListPage

    #         print("[INFO] SAR 月報一覧画面を開きます")
    #         self.click_header_menu("name3")
    #         return SarMonthlyListPage(self.page)

    #     def click_header_menu(self, menu_id: str) -> None:
    #         """SAR ヘッダーメニューの項目をクリックする。

    #         Args:
    #             menu_id: ヘッダーメニュー項目の ID。
    #         """
    #         menu_locator = self.page.locator(f"#{menu_id}")
    #         expect(menu_locator).to_be_visible()
    #         menu_locator.click()
    #         self.wait_for_footer()

    def wait_for_footer(self, timeout: int = 10000) -> None:
        print("[INFO] SAR フッター表示を待機します")
        self.page.locator("#dctp_footer").wait_for(state="attached", timeout=timeout)
        self.page.wait_for_timeout(1000)
