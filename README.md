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
### 6.0. Wails GUI（開発中）
```powershell
cd desktop
wails build
./build/bin/desktop.exe
```
Go、Node.js、Wails CLI、WebView2 が必要です。画面は最大化して開き、月〜日の7行で全項目を1日1行で編集できます。チェックした日だけを登録できます。よく使う入力は日付を除いて保存され、画面上部の「よく使う入力を編集」からタイトルと内容を変更できます。データは既存の `work_record_presets.json` と共通です。登録時のみ既存の Python 処理を呼び出します。`env.ps1` と `.venv` は従来どおりリポジトリ直下に置いてください。
今日の日付は画面上部に表示されます。出力する `work_records.yaml` の項目順は `target_date`、`work_segment`、時刻・休憩・交通費・備考、SAR項目の順で固定です。

### 6.1. GUIから登録（1週間分）
```bash
./create_work_record_gui.bat
# → 週の開始日を選び、登録したい日にチェックを入れて各日を編集する。
# → 「保存」でチェックした日だけを work_records.yaml に出力し、HRMOS と SAR に登録する。
# → よく使う1日分の入力は名前を付けて保存・適用できる。日付は保存されない。
# → 保存した入力はローカルの work_record_presets.json に保持され、Git の管理対象外。
```

### 6.2. 一括登録
```bash
# 「work_records.yaml」は6.1を実施すると生成されるためその内容を書き換えること。records属性の子要素を必要な日数分記述する。
# 6.1を実施した際、「work_records.yaml」の内容が上書きされるため、GUI登録と手動の一括登録を使い分ける場合は要注意。
./env.ps1
python ./src/main.py --input ./work_records.yaml
```
