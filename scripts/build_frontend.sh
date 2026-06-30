#!/usr/bin/env bash
# SPA をビルドして ../sample-gui/statics へ出力する。
set -euo pipefail

FRONTEND_DIR="${FRONTEND_DIR:-../sample-gui-frontend}"

cd "$(dirname "$0")/.."
cd "$FRONTEND_DIR"

if [ -d node_modules ]; then
  npm run build
else
  npm ci && npm run build
fi

echo "SPA build complete -> sample-gui/statics/"
