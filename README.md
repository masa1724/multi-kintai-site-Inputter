# HRMOS と SAR に勤怠情報を1操作で纏めて登録するツール

## 1. 仮想環境を作成
```bash
python -m venv .venv
```

## 2. 仮想環境を有効化
```bash
./.venv/Scripts/Activate.ps1
```

## 3. 依存関係インストール
```bash
pip install -r requirements.txt
```

## 4. playwrightが自動操作で利用するブラウザバイナリをインストール
```bash
playwright install
```

## 5. 環境設定ファイル「./env.ps1」の値を書き換える
```bash
copy ./env.ps1.example ./env.ps1
notepad ./env.ps1
```

## 6. 実行
### 6.1. Wails GUI
```powershell
./create_work_record_gui.bat
```
同梱の `desktop/build/bin/desktop.exe` を起動します。ソースから再ビルドする場合は `desktop` ディレクトリで `wails build` を実行してください。再ビルドにはGo、Node.js、Wails CLI、WebView2が必要です。画面は最大化して開き、月〜日の7行で全項目を1日1行で編集できます。チェックした日だけを登録できます。よく使う入力は日付を除いて保存され、画面上部の「よく使う入力を編集」からタイトルと内容を変更できます。データは既存の `work_record_presets.json` と共通です。登録時のみ既存の Python 処理を呼び出します。`env.ps1` と `.venv` は従来どおりリポジトリ直下に置いてください。
今日の日付は画面上部に表示されます。出力する `work_records.yaml` の項目順は `target_date`、`work_segment`、時刻・休憩・交通費・備考、SAR項目の順で固定です。

### 6.2. 一括登録
```bash
# 「work_records.yaml」はGUI登録で生成されるためその内容を書き換えること。records属性の子要素を必要な日数分記述する。
# GUI登録を実施すると「work_records.yaml」が上書きされるため、手動の一括登録と使い分ける場合は要注意。
./env.ps1
python ./src/main.py --input ./work_records.yaml
```
