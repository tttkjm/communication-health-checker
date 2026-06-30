# communication_health_checker — 並列Ping監視ツール

ネットワークエンジニア向けに、複数ターゲット機器へ並列で ping を打ち、結果ログをターゲット毎に管理するデスクトップ配布アプリ。

- **バックエンド**: Python 3.14 + FastAPI + DDD/Clean Architecture + Pydantic v2（このリポジトリ）
- **フロントエンド**: React + MUI（別リポジトリ `../sample-gui-frontend`）。ビルド成果物を `statics/` に配置し FastAPI が配信。
- **配布**: PyInstaller シングルバイナリ。起動するとローカル FastAPI が立ち上がり、ブラウザが自動で開く。

設計の詳細は [`docs/architecture.md`](docs/architecture.md) を参照。

## 機能

ping は 3 つの実行モードを持つ（いずれも複数ターゲットへ並列送信）:

1. **ワンショット実行** — パラメータなしで **1 回だけ**送信（REST 応答で結果返却）
2. **定期実行** — **周期のみ**設定し、周期ごとに 1 回送信して停止するまで継続（WebSocket でライブ表示）
3. **複数回実行** — **回数のみ**設定し、**1 秒ごと**に送信して指定回数で自動終了（WebSocket でライブ表示）

定期 / 複数回はバックエンド駆動（サーバ側 asyncio タスク）。加えて:

4. **ターゲット機器 CRUD** — 登録 / 取得 / 一覧 / 更新 / 削除 / 全削除（SQLite 永続化）

## セットアップ

```bash
uv sync --extra desktop --extra dev --extra test
```

## 開発実行

```bash
uv run python -m apps.desktop.main          # ブラウザが自動で開く
# 固定ポート + ブラウザ抑止（フロント dev サーバから接続する場合）:
COMMUNICATION_HEALTH_CHECKER_PORT=8765 COMMUNICATION_HEALTH_CHECKER_NO_BROWSER=1 uv run python -m apps.desktop.main
```

環境変数: `COMMUNICATION_HEALTH_CHECKER_HOST`(既定 127.0.0.1) / `COMMUNICATION_HEALTH_CHECKER_PORT`(既定 8765、使用中なら空きポート) / `COMMUNICATION_HEALTH_CHECKER_NO_BROWSER=1` / `COMMUNICATION_HEALTH_CHECKER_FORCE_NEW=1`(シングルインスタンス判定を無視して強制起動) / `SQLITE_DB_PATH`(既定 `~/.communication_health_checker/communication_health_checker.db`、テストは `:memory:`)

### シングルインスタンス動作
- 既に communication_health_checker が起動中の状態で再度起動すると、**新しいサーバは立てず**、既存サーバの URL をブラウザで開くだけで終了します（GUI のタブを閉じてから開き直してもプロセスは増えません）。
- 起動中インスタンスは `~/.communication_health_checker/instance.json`(host/port/pid) に記録され、正常終了時に削除されます。プロセスが強制終了されても、次回起動時にヘルスチェック(`GET /api/v1/system/health`)で死活判定するためスタリングしません。
- GUI 右上の「**サーバ終了**」ボタン、または `POST /api/v1/system/shutdown` でサーバを正常終了できます。

## テスト & 静的解析

```bash
uv run pytest -q                            # 全テスト
uv run pytest -m "not slow" -q              # 実 ping を除く
uv run ruff check src/ apps/ tests/
uv run ruff format src/ apps/ tests/
```

## ビルド（配布バイナリ）

```bash
bash scripts/build_app.sh                   # フロントビルド → 依存解決 → PyInstaller
# => dist/communication_health_checker(.exe)
```

> ローカル localhost を社内プロキシが横取りする環境では、ブラウザの localhost バイパス設定／`NO_PROXY=127.0.0.1,localhost` を確認すること。

## API 概要

| メソッド | パス | 説明 |
|---|---|---|
| GET/POST | `/api/v1/targets` | 一覧取得 / 登録 |
| GET/PUT/DELETE | `/api/v1/targets/{id}` | 取得 / 更新 / 削除 |
| DELETE | `/api/v1/targets` | 全削除 |
| POST | `/api/v1/ping/run` | ワンショット実行（1 回だけ） |
| GET | `/api/v1/ping/logs/{id}` | ターゲット毎ログ |
| POST | `/api/v1/ping/schedule/periodic` | 定期実行開始（周期のみ） |
| POST | `/api/v1/ping/schedule/repeat` | 複数回実行開始（回数のみ・1 秒間隔） |
| POST | `/api/v1/ping/schedule/stop` | スケジュール停止（定期 / 複数回 共通） |
| GET | `/api/v1/ping/schedule/status` | スケジュール状態 |
| WS | `/ws/ping` | スケジュール ping 結果のライブ配信 |
| GET | `/api/v1/system/health` | ヘルスチェック（シングルインスタンス判定） |
| POST | `/api/v1/system/shutdown` | サーバを正常終了 |

OpenAPI ドキュメントは起動後 `http://127.0.0.1:<port>/docs`。
