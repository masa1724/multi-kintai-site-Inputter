from playwright.sync_api import Page

from utils import masking
from sar.sar_base_page import SarBasePage
from sar.sar_daily_list_page import SarDailyListPage


class SarLoginPage(SarBasePage):
    """SAR ログイン画面のページオブジェクト。"""

    def __init__(self, page: Page, login_url: str):
        super().__init__(page)
        self.login_url = login_url

    def open(self):
        """ログイン画面を開く。"""
        print("[INFO] SAR ログイン画面を開きます")
        self.page.goto(self.login_url)
        return self

    def login(self, user_id: str, password: str) -> SarDailyListPage:
        """認証情報を入力してログインし、日報一覧画面を返す。"""
        print("[INFO] SAR ログイン処理を開始します")

        print(f"[INFO] SAR ログインIDを入力します: {masking(user_id)}")
        self.page.get_by_role(
            "textbox", name="ユーザ名 <ユーザ ID>@<ドメイン ID>"
        ).fill(user_id)

        print(f"[INFO] SAR パスワードを入力します: {masking(password)}")
        self.page.locator('input[name="password"]').fill(password)

        print("[INFO] SAR ログインボタンをクリックします")
        self.page.get_by_role("button", name="ログイン").click()

        print("[INFO] SAR ログイン処理が完了しました")
        print("[INFO] SAR 日報一覧を開きます")
        self.wait_for_footer()
        return SarDailyListPage(self.page)
