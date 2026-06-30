#!/usr/bin/env bash
# SPA をビルドして statics/ へ出力する。
# フロントエンドのソースは別リポジトリ ($FRONTEND_DIR、既定 ../sample-gui-frontend)。
# ソースが無い場合は、本リポジトリに同梱済みの statics/ をそのまま使ってビルドを続行する。
set -euo pipefail

FRONTEND_DIR="${FRONTEND_DIR:-../sample-gui-frontend}"

cd "$(dirname "$0")/.."

if [ ! -d "$FRONTEND_DIR" ]; then
  if [ -f statics/index.html ]; then
    echo "フロントエンドリポジトリ ($FRONTEND_DIR) が見つかりません。"
    echo "同梱済みの statics/ を使用してビルドを続行します。"
    echo "（最新の SPA を取り込む場合は FRONTEND_DIR でパスを指定してください）"
    exit 0
  fi
  echo "エラー: フロントエンドリポジトリ ($FRONTEND_DIR) が無く、同梱の statics/ もありません。" >&2
  echo "FRONTEND_DIR 環境変数でフロントエンドのパスを指定してください。" >&2
  exit 1
fi

cd "$FRONTEND_DIR"

if [ -d node_modules ]; then
  npm run build
else
  npm ci && npm run build
fi

echo "SPA build complete -> statics/"
