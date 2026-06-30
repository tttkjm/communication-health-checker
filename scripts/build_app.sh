#!/usr/bin/env bash
# フロントビルド → 依存解決 → PyInstaller でシングルバイナリ生成。
# 生成物: dist/communication_health_checker (Windows では dist/communication_health_checker.exe)
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> 1/3 フロントエンドをビルド"
bash scripts/build_frontend.sh

echo "==> 2/3 バックエンド依存を解決"
uv sync --extra desktop --extra build

echo "==> 3/3 PyInstaller でパッケージング"
uv run pyinstaller communication_health_checker.spec --clean --noconfirm

echo "完了: dist/ を確認してください。"
