import os

# 全テストでインメモリ SQLite を使う（import 前に設定する必要がある）
os.environ.setdefault("SQLITE_DB_PATH", ":memory:")

import pytest  # noqa: E402

from communication_health_checker.modules.desktop_module import DesktopModule  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_di() -> None:
    """各テストで DI シングルトン（= インメモリ DB）をリセットする。"""
    DesktopModule.reset()
    yield
    DesktopModule.reset()
