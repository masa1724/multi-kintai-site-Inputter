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
### 6.1. GUIから登録（1件登録のみ）
```bash
./create_work_record_gui.bat
# → 「create_work_record_gui.ps1」と同じフォルダ配下に勤怠情報1件の「work_records.yaml」が生成され、そのファイルがmain.pyの入力となる。
```

### 6.2. 一括登録
```bash
# 「work_records.yaml」は6.1を実施すると生成されるためその内容を書き換えること。records属性の子要素を必要な日数分記述する。
# 6.1を実施した際、「work_records.yaml」の内容が上書きされるため、1件登録と一括登録を使い分ける場合は要注意。
./env.ps1
python ./src/main.py --input ./work_records.yaml
```
