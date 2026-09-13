# HRMOS・SAR 勤怠一括登録ツール

Windows 向けの Wails GUI で最大 7 日分の勤怠を 1 日 1 行で入力し、チェックした日を HRMOS と SAR に登録します。GUI は `desktop/build/bin/desktop.exe` を同梱していますが、登録処理にはリポジトリ内の Python コードを使用します。

以下のコマンドは、特記がなければ **リポジトリ直下の PowerShell** で実行してください。

## 利用するための準備（Go・Node.js・Wails CLI は不要）

1. Windows に [WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/) があることを確認します。Wails GUI の表示に必要です。[Wails の Windows 向け導入ガイド](https://wails.io/docs/gettingstarted/installation/)
2. [Python](https://www.python.org/downloads/windows/) をインストールし、`python --version` で利用できることを確認します。仮想環境、依存パッケージ、自動操作用の Chromium を準備します。

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m playwright install chromium
   ```

   このツールは Playwright の Chromium を使います。[Playwright のブラウザー導入手順](https://playwright.dev/python/docs/browsers)

3. 認証情報の設定ファイルを作り、各項目を実際の値に置き換えます。

   ```powershell
   Copy-Item .\env.ps1.example .\env.ps1
   notepad .\env.ps1
   ```

   `env.ps1` は秘密情報を含むため Git の登録対象から除外しています。共有・コミットしないでください。

## 起動と登録

```powershell
.\create_work_record_gui.bat
```

バッチファイルは同梱の `desktop/build/bin/desktop.exe` を起動します。画面は最大化して開き、月～日の 7 行に全項目を表示します。登録対象の行をチェックして登録してください。選択した内容で `work_records.yaml` が**上書き**され、その後 Python によるブラウザー操作が実行されます。したがって exe 単体では登録できず、リポジトリ直下の `.venv`、`env.ps1`、`src` が必要です。

「よく使う入力」は日付を除いて `work_record_presets.json` に保存され、画面上部からタイトルと内容を編集できます。今日の日付も画面上部に表示されます。プリセットと YAML、既定値の `work_record_defaults.json` は Git の登録対象から除外しています。

### YAML を直接編集して一括登録する場合

`work_records.yaml` の `records` に登録対象の日数分を記載した後、次を実行します。GUI から登録するとこのファイルは上書きされるため、手動編集した内容が必要なら先にバックアップしてください。

```powershell
. .\env.ps1
.\.venv\Scripts\python.exe .\src\main.py --input .\work_records.yaml
```

## Wails GUI をソースから再ビルドする場合

通常の起動にはこの節のツールは不要です。ソース変更時のみ、次を準備してください。

1. [Go の Windows 版](https://go.dev/doc/install)をインストールします。このリポジトリの `desktop/go.mod` は **Go 1.25.0** を指定しています。インストール後、新しい PowerShell で `go version` を確認してください。
2. [Node.js](https://nodejs.org/en/download) をインストールし、`node --version` と `npm --version` を確認します。フロントエンドは Vite 7 を使用し、Node.js **20.19+ または 22.12+** が必要です。[Vite 公式要件](https://vite.dev/guide/)
3. `go.mod` と同じ Wails v2.15.0 の CLI をインストールし、環境を確認します。`wails` が認識されないときは Go のバイナリ配置先（`go env GOPATH` で確認できるディレクトリの `bin`）を `PATH` に追加し、PowerShell を開き直してください。[Wails 公式導入手順](https://wails.io/docs/gettingstarted/installation/)

   ```powershell
   go install github.com/wailsapp/wails/v2/cmd/wails@v2.15.0
   wails doctor
   ```

4. `desktop` でビルドします。`desktop/wails.json` の設定によりフロントエンドの依存関係もインストールされます。生成先は `desktop/build/bin/desktop.exe` です。

   ```powershell
   Set-Location .\desktop
   wails build
   ```

開発時のライブ起動は同じ `desktop` ディレクトリで `wails dev` を実行します。ビルド済み exe は Git の登録対象なので、再ビルドで変更された場合は差分を確認してください。
