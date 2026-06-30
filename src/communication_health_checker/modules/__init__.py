"""DI コンテナのエントリーポイント。"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from injector import Injector


def get_di_container() -> "Injector":
    from communication_health_checker.modules.desktop_module import DesktopModule

    return DesktopModule.get_instance()
