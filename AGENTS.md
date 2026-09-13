# エージェント向け作業メモ

このファイルは、このリポジトリを編集するエージェント向けの、現行実装に基づく注意事項です。利用者向けの導入・起動手順は [README.md](README.md) を参照してください。

## 構成と実行経路

- Windows 専用の Wails v2 + React/TypeScript GUI。`create_work_record_gui.bat` は `desktop/build/bin/desktop.exe` を起動する。
- GUI 側は `desktop/frontend/src/`、Go バックエンドは `desktop/app.go`。Go の `RegisterRecords` は選択済み 1～7 日分を `work_records.yaml` に書き、PowerShell で `env.ps1` を読み込んでから `.venv/Scripts/python.exe src/main.py --input work_records.yaml` を呼ぶ。
- Python の自動操作は `src/` にあり、Playwright Chromium で HRMOS と SAR の外部サービスを操作する。**実サービスへの登録は副作用を伴う**ため、検証目的で安易に実行しない。
- プロジェクトルートは Go 側で `src/main.py` を目印に検出する。GUI の exe だけを別フォルダに移しても登録機能は動かない。

## データと秘密情報

- `env.ps1` は認証情報を含み、Git では除外。`env.ps1.example` をひな形として使い、実値をコミット・ログ出力しない。
- `work_record_presets.json` は「よく使う入力」、`work_record_defaults.json` は初期値。どちらもルート直下のローカルファイルで Git 除外。プリセットは日付を保存しない。
- GUI 登録時に `work_records.yaml` を上書きする。手動編集した YAML の保護が必要な変更ではこの挙動に注意する。
- YAML のフィールド順は `desktop/app.go` の `recordFieldOrder` で固定。フィールド追加・名称変更時はフロントエンド、Go、Python の読み込み側とテストを合わせて確認する。

## 変更・検証の目安

- Go: `Set-Location desktop; go test ./...`
- フロントエンド: `Set-Location desktop/frontend; npm ci; npm run build`
- GUI 実行・ビルド: ルート README の手順を参照。`desktop/build/bin/desktop.exe` は意図的に Git 管理されているため、再ビルド後はバイナリ差分の有無を確認する。
- 自動テストは外部の HRMOS・SAR に接続しない範囲で実施する。認証情報・個人データをテストに埋め込まない。
