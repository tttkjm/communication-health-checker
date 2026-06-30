from abc import ABC, abstractmethod

from communication_health_checker.domain.models.ping.ping_probe import PingProbe


class PingPort(ABC):
    """ICMP ping を実行する外部依存ポート（blocking）。"""

    @abstractmethod
    def ping_once(self, host: str, count: int, timeout_ms: int) -> list[PingProbe]:
        """host へ count 回 ping を送り、各回の結果を返す（長さ == count）。"""
