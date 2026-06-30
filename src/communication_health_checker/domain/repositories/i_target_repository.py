from abc import ABC, abstractmethod

from communication_health_checker.domain.models.target.target import Target
from communication_health_checker.domain.models.target.target_id import TargetId


class ITargetRepository(ABC):
    """ターゲット機器の永続化リポジトリ。"""

    @abstractmethod
    def save(self, target: Target) -> None:
        """新規作成または更新（upsert）。"""

    @abstractmethod
    def find_by_id(self, target_id: TargetId) -> Target | None: ...

    @abstractmethod
    def find_all(self) -> list[Target]: ...

    @abstractmethod
    def exists(self, target_id: TargetId) -> bool: ...

    @abstractmethod
    def delete(self, target_id: TargetId) -> None: ...

    @abstractmethod
    def delete_all(self) -> None: ...
