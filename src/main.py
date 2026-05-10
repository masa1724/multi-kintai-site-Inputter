import argparse

from playwright.sync_api import sync_playwright

from hrmos.hrmos_login_page import HrmosLoginPage
from hrmos.hrmos_work_record import HrmosWorkRecord
from sar.sar_daily_record import SarDailyRecord, convert_to_sar_daily_record
from sar.sar_login_page import SarLoginPage
from utils import get_required_env
from work_record_loader import load_input_records, validate_input_records
from work_record import WorkRecord
from hrmos.hrmos_work_record import convert_to_harmos_work_record


def main():
    # 環境変数の取得
    hrmos_login_url = get_required_env("HRMOS_LOGIN_URL")
    hrmos_login_id = get_required_env("HRMOS_LOGIN_ID")
    hrmos_password = get_required_env("HRMOS_PASSWORD")
    sar_login_url = get_required_env("SAR_LOGIN_URL")
    sar_login_id = get_required_env("SAR_LOGIN_ID")
    sar_password = get_required_env("SAR_PASSWORD")

    # コマンドライン引数の解析
    print("[INFO] コマンドライン引数の解析")
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="入力 YAML ファイルパス")
    args = parser.parse_args()
    print("[INFO] コマンドライン引数の解析が完了")

    # 入力ファイルの読込
    print("[INFO] 入力ファイルの読込")
    work_records: list[WorkRecord] = load_input_records(args.input)
    print(f"[INFO] 入力ファイルの読込が完了。入力レコード数: {len(work_records)}")

    # 入力レコードのバリデーションチェック
    print("[INFO] 入力レコードのバリデーションチェック")
    validate_input_records(work_records)
    print("[INFO] 入力レコードのバリデーションチェックが完了")

    with sync_playwright() as p:
        # ブラウザを起動する（headless=False でブラウザを表示する）
        browser = p.chromium.launch(headless=False)

        # 入力ファイルの内容をもとに、HRMOSの勤怠情報を作成
        hrmos_work_records: list[HrmosWorkRecord] = []
        for record in work_records:
            hrmos_work_records.append(
                convert_to_harmos_work_record(record),
            )

        # 入力ファイルの内容をもとに、SARの勤怠情報を作成
        sar_daily_records: list[SarDailyRecord] = []
        for record in work_records:
            sar_daily_records.append(convert_to_sar_daily_record(record))

        hrmos_input = True
        sar_input = True

        # HRMOSの勤怠情報を入力
        if hrmos_work_records and hrmos_input:
            # ログイン画面を開く
            hrmos_page = browser.new_page()
            hrmos_login_page = HrmosLoginPage(hrmos_page, hrmos_login_url).open()

            # ログインする（勤怠一覧画面に遷移する）
            hrmos_works_page = hrmos_login_page.login(hrmos_login_id, hrmos_password)

            for work_info in hrmos_work_records:
                # 対象月の勤怠一覧画面に遷移
                target_month = work_info.target_date.strftime("%Y-%m")
                hrmos_works_page = hrmos_works_page.go_month(target_month)

                # 対象日の勤怠編集画面に遷移
                target_day = int(work_info.target_date.strftime("%d"))
                work_edit_page = hrmos_works_page.open_work_by_day(target_day)

                # 勤怠編集画面に勤怠情報を入力
                work_edit_page.input_work_fields(work_info)

                # 勤怠編集画面の申請ボタンをクリック（申請後は勤怠一覧画面に遷移する）
                hrmos_works_page = work_edit_page.apply()

                # 入力内容を目視確認するため、少し待機する
                # hrmos_page.wait_for_timeout(5000)
                # hrmos_page.wait_for_timeout(500)

            # ページを閉じる
            hrmos_page.close()

        # SARの勤怠情報を入力
        if sar_daily_records and sar_input:
            # ログイン画面を開く
            sar_page = browser.new_page()
            sar_login_page = SarLoginPage(sar_page, sar_login_url).open()

            # ログインする（日報一覧画面に遷移する）
            sar_daily_list_page = sar_login_page.login(sar_login_id, sar_password)

            for work_info in sar_daily_records:
                # 対象の日報レコードの存在確認
                if sar_daily_list_page.has_daily_link(work_info.target_date):
                    # 対象日のレコードが既に作成されている場合は、日報の編集画面に遷移する
                    sar_daily_edit_page = sar_daily_list_page.go_to_daily_edit(
                        work_info.target_date
                    )
                else:
                    # 対象日のレコードが未作成の場合は、日報を新規作成してから編集画面に遷移する
                    sar_daily_edit_page = sar_daily_list_page.createEmptyDailyRecord(
                        work_info.target_date
                    )

                # 日報編集画面に勤怠情報を入力
                sar_daily_edit_page.input_daily_fields(work_info)

                # 日報編集画面の登録ボタンをクリック（登録後は日報一覧画面に遷移する）
                sar_daily_edit_page.register()

                # 入力内容を目視確認するため、少し待機する
                # sar_page.wait_for_timeout(5000)
                # sar_page.wait_for_timeout(500)

            # ページを閉じる
            sar_page.close()

        # ブラウザを閉じる
        browser.close()


if __name__ == "__main__":
    main()
