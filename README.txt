## 1. 仮想環境（推奨）を作成
python -m venv .venv

## 2. 有効化
.\.venv\Scripts\Activate.ps1

## 3. 依存関係インストール
pip install -r requirements.txt

## 4. playwrightのブラウザをインストール
playwright install

## 5. 「./env.ps1」の値を書き換える
copy ./env.ps1.example ./env.ps1
notepad ./env.ps1

## 6. 「./work_records.yaml」の値を書き換える　※一括登録を利用する場合のみ
copy ./work_records.yaml.example ./work_records.yaml
notepad ./work_records.yaml

## 7. 実行
### 7.1. GUIから登録（1件登録のみ）
./create_work_record_gui.bat

### 7.2. 一括登録
./env.ps1
python ./src/main.py --input ./work_records.yaml

