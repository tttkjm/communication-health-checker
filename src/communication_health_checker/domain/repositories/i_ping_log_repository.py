from abc import ABC, abstractmethod

from communication_health_checker.domain.models.ping.ping_log import PingLog
from communication_health_checker.domain.models.target.target_id import TargetId


class IPingLogRepository(ABC):
    """ping ログの永続化リポジトリ。"""

    @abstractmethod
    def append_many(self, logs: list[PingLog]) -> None: ...

    @abstractmethod
    def find_by_target(self, target_id: TargetId, limit: int = 200) -> list[PingLog]:
        """指定ターゲットの最新ログを新しい順に返す。"""

    @abstractmethod
    def clear_by_target(self, target_id: TargetId) -> None: ...

    @abstractmethod
    def clear_all(self) -> None: ...
