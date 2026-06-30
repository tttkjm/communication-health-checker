import sys
from pathlib import Path


def resource_path(relative: str) -> Path:
    """同梱リソースの絶対パスを返す。

    - PyInstaller 実行時: sys._MEIPASS 配下から解決
    - 開発実行時:        プロジェクトルート（このファイルの 2 階層上）から解決
    """
    base = getattr(sys, "_MEIPASS", None)
    if base is not None:
        return Path(base) / relative
    return Path(__file__).resolve().parents[2] / relative
