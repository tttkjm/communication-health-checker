#!/usr/bin/env bash
# SPA を statics/ に用意する。
#
# 標準動作: 本リポジトリに同梱済みの statics/（ビルド済み SPA）をそのまま使い、再ビルドしない。
# 再ビルド  : REBUILD_FRONTEND=1 のときのみ、フロントエンドのソース
#             ($FRONTEND_DIR、既定 ../sample-gui-frontend) を npm でビルドする。
set -euo pipefail

FRONTEND_DIR="${FRONTEND_DIR:-../sample-gui-frontend}"
REBUILD_FRONTEND="${REBUILD_FRONTEND:-0}"

cd "$(dirname "$0")/.."

if [ "$REBUILD_FRONTEND" != "1" ]; then
  # --- 標準動作: 同梱の statics/ を使用 ---
  if [ -f statics/index.html ]; then
    echo "同梱済みの statics/ を使用します（フロントエンドの再ビルドはスキップ）。"
    echo "再ビルドする場合は REBUILD_FRONTEND=1 を指定してください。"
    exit 0
  fi
  echo "エラー: 同梱の statics/ が見つかりません。" >&2
  echo "REBUILD_FRONTEND=1 でフロントエンドを再ビルドするか、statics/ を用意してください。" >&2
  exit 1
fi

# --- 再ビルド: フロントエンドのソースから npm ビルド ---
if [ ! -d "$FRONTEND_DIR" ]; then
  echo "エラー: フロントエンドリポジトリ ($FRONTEND_DIR) が見つかりません。" >&2
  echo "FRONTEND_DIR 環境変数でフロントエンドのパスを指定してください。" >&2
  exit 1
fi

echo "フロントエンドを再ビルドします: $FRONTEND_DIR"
cd "$FRONTEND_DIR"

if [ -d node_modules ]; then
  npm run build
else
  npm ci && npm run build
fi

echo "SPA build complete -> statics/"
