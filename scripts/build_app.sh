#!/usr/bin/env bash
# フロント準備 → 依存解決 → PyInstaller でシングルバイナリ生成。
# 生成物: dist/communication_health_checker (Windows では dist/communication_health_checker.exe)
#
# 標準動作: 同梱済みの statics/ をそのまま使う（フロントエンドの再ビルドはしない）。
# オプション:
#   --rebuild-frontend, -r   フロントエンドのソースから SPA を再ビルドする
#                            （= REBUILD_FRONTEND=1。ソースは FRONTEND_DIR、既定 ../sample-gui-frontend）
set -euo pipefail

cd "$(dirname "$0")/.."

REBUILD_FRONTEND="${REBUILD_FRONTEND:-0}"
for arg in "$@"; do
  case "$arg" in
    --rebuild-frontend|-r) REBUILD_FRONTEND=1 ;;
    -h|--help)
      echo "Usage: bash scripts/build_app.sh [--rebuild-frontend|-r]"
      exit 0
      ;;
    *)
      echo "不明な引数: $arg" >&2
      echo "Usage: bash scripts/build_app.sh [--rebuild-frontend|-r]" >&2
      exit 2
      ;;
  esac
done
export REBUILD_FRONTEND

if [ "$REBUILD_FRONTEND" = "1" ]; then
  echo "==> 1/3 フロントエンドを再ビルド"
else
  echo "==> 1/3 フロントエンド（同梱の statics/ を使用）"
fi
bash scripts/build_frontend.sh

echo "==> 2/3 バックエンド依存を解決"
uv sync --extra desktop --extra build

echo "==> 3/3 PyInstaller でパッケージング"
uv run pyinstaller communication_health_checker.spec --clean --noconfirm

echo "完了: dist/ を確認してください。"
