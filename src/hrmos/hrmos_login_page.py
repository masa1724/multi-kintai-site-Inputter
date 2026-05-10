from hrmos.hrmos_works_page import HrmosWorksPage

from utils import masking


class HrmosLoginPage:
    """HRMOS ログイン画面のページオブジェクト。"""

    def __init__(self, page, login_url: str):
        self.page = page
        self.login_url = login_url

    def open(self):
        print("[INFO] HRMOS ログイン画面を開きます")
        self.page.goto(self.login_url)
        return self

    def login(self, user_id: str, password: str) -> "HrmosWorksPage":
        """認証情報を入力してログインし、遷移後の勤怠一覧ページを返す。"""
        print("[INFO] HRMOS ログイン処理を開始します")

        print(f"[INFO] HRMOS ログインIDを入力します: {masking(user_id)}")
        self.page.get_by_role("textbox", name="ログインID").fill(user_id)

        print(f"[INFO] HRMOS パスワードを入力します: {masking(password)}")
        self.page.get_by_role("textbox", name="パスワード").fill(password)

        print("[INFO] HRMOS ログインボタンをクリックします")
        self.page.get_by_role("button", name="ログイン").click()

        print("[INFO] HRMOS ログイン処理が完了しました")

        print("[INFO] HRMOS 勤怠一覧を開きます")
        return HrmosWorksPage(self.page)
