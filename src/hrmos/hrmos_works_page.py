from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from hrmos.hrmos_work_edit_page import HrmosWorkEditPage


class HrmosWorksPage:
    """HRMOS 勤怠一覧画面のページオブジェクト。"""

    def __init__(self, page: Page):
        self.page = page

    def go_month(self, year_month: str) -> "HrmosWorksPage":
        """YYYY-MM 形式で指定された月の勤怠一覧を開く。"""
        print(f"[INFO] HRMOS 勤怠一覧で対象月を開きます: {year_month}")
        self.page.goto(f"https://f.ieyasu.co/works?date={year_month}")
        expect(self.page.locator("#editGraphTable")).to_be_visible()
        print(f"[INFO] HRMOS 勤怠一覧の対象月を開きました: {year_month}")
        return self

    def open_work_by_day(self, day: int) -> "HrmosWorkEditPage":
        """
        現在表示中の月から指定日の編集画面を開く。

        承認済みの勤怠は編集できないためエラーにし、申請中の勤怠は申請取消後に
        行を取り直してから編集画面を開く。
        """

        if not 1 <= day <= 31:
            raise ValueError(f"day は 1〜31 で指定してください: {day}")

        row = self._get_row_by_day(day)
        status = self._get_application_status(row)

        print(f"[INFO] HRMOS {day:02d}日 の申請状態: {status}")

        if status == "承認済み":
            message = f"[ERROR] HRMOS {day:02d}日 は承認済みのため、申請解除できず編集できません。"
            print(message)
            raise RuntimeError(message)

        if status == "申請中":
            print(f"[INFO] HRMOS {day:02d}日 は申請中のため、申請解除を開始します。")
            self._cancel_application(row, day)

            # 申請取消で一覧の要素ツリーが更新されるため、古い行の取得結果を使い回さない。
            row, status_after_cancel = self._wait_for_status_after_cancel(day)
            print(f"[INFO] HRMOS {day:02d}日 の申請解除後の状態: {status_after_cancel}")

            if status_after_cancel == "申請中":
                print(
                    f"[WARN] HRMOS {day:02d}日 は一覧上まだ申請中に見えますが、"
                    "編集画面を開ける可能性があるため処理を続行します。"
                )

            if status_after_cancel == "承認済み":
                message = (
                    f"[ERROR] HRMOS {day:02d}日 は承認済みに見えるため編集できません。"
                )
                print(message)
                raise RuntimeError(message)

        self._open_edit_screen(row, day)

        print(f"[INFO] HRMOS {day:02d}日 の編集画面を開きました。")
        return HrmosWorkEditPage(self.page)

    def _get_row_by_day(self, day: int):
        """勤怠一覧テーブルから指定日の行を取得する。"""
        day_text = f"{day:02d}"
        expect(self.page.locator("#editGraphTable")).to_be_visible()

        rows = self.page.locator(
            "#editGraphTable tr",
            has=self.page.locator(f"td.cellDate span.date:text-is('{day_text}')"),
        )

        if rows.count() == 0:
            raise ValueError(f"HRMOS {day_text}日 の行が見つかりませんでした")

        row = rows.first
        expect(row).to_be_visible()
        return row

    def _get_application_status(self, row) -> str:
        """一覧行のボタンやラベルから、申請状態をざっくり判定する。"""
        if row.locator("td.cellBtn").get_by_text("承認済み").count() > 0:
            return "承認済み"

        if row.get_by_role("link", name="申請取消").count() > 0:
            return "申請中"

        if row.get_by_role("button", name="申請取消").count() > 0:
            return "申請中"

        return "未申請"

    def _cancel_application(self, row, day: int) -> None:
        """申請中の行に表示される申請取消操作を実行する。"""
        cancel_link = row.get_by_role("link", name="申請取消")
        cancel_button = row.get_by_role("button", name="申請取消")

        if cancel_link.count() > 0:
            target = cancel_link.first
        elif cancel_button.count() > 0:
            target = cancel_button.first
        else:
            message = f"[ERROR] HRMOS {day:02d}日 は申請中と判定しましたが、申請取消ボタンが見つかりませんでした。"
            print(message)
            raise RuntimeError(message)

        expect(target).to_be_visible()
        print(f"[INFO] HRMOS {day:02d}日 の申請解除ボタンを押します。")
        target.click()

        confirm_button = self.page.get_by_role("button", name="はい")
        try:
            confirm_button.wait_for(state="visible", timeout=3000)
            print(
                f"[INFO] HRMOS {day:02d}日 の申請解除確認ダイアログで「はい」を押します。"
            )
            confirm_button.click()
        except PlaywrightTimeoutError:
            print(
                f"[WARN] HRMOS {day:02d}日 の申請解除確認ダイアログは表示されませんでした。"
            )

        expect(self.page.locator("#editGraphTable")).to_be_visible()
        print(f"[INFO] HRMOS {day:02d}日 の申請解除処理が完了しました。")

    def _wait_for_status_after_cancel(self, day: int):
        row = self._get_row_by_day(day)
        status = self._get_application_status(row)

        for _ in range(10):
            if status != "申請中":
                return row, status

            self.page.wait_for_timeout(500)
            row = self._get_row_by_day(day)
            status = self._get_application_status(row)

        return row, status

    def _open_edit_screen(self, row, day: int) -> None:
        """日付セルを起点に、画面構造の違いを吸収しながら編集画面を開く。"""
        date_cell = row.locator("td.cellDate").first
        expect(date_cell).to_be_visible()

        print(f"[INFO] HRMOS {day:02d}日 の日付セルをクリックします。")
        date_cell.click(force=True)

        if self._wait_edit_screen():
            return

        # 日付セル自体のクリックで遷移しない画面では、セル内リンクを試す。
        link = date_cell.get_by_role("link")
        if link.count() > 0:
            print(f"[INFO] HRMOS {day:02d}日 の日付セル内リンクをクリックします。")
            link.first.click()
            if self._wait_edit_screen():
                return

        # 古いレイアウトでは work_edit_xxx 要素が実際のクリック対象になる。
        edit_target = row.locator("td.cellDate div[id^='work_edit_']").first
        if edit_target.count() > 0:
            print(f"[INFO] HRMOS {day:02d}日 の編集ターゲット要素をクリックします。")
            edit_target.click(force=True)
            if self._wait_edit_screen():
                return

        raise RuntimeError(
            f"[ERROR] HRMOS {day:02d}日 の編集画面へ遷移できませんでした。"
        )

    def _wait_edit_screen(self) -> bool:
        """編集フォームの勤務区分セレクトが見えれば遷移完了とみなす。"""
        try:
            self.page.locator("#work_segment_id").wait_for(
                state="visible", timeout=3000
            )
            return True
        except PlaywrightTimeoutError:
            return False
