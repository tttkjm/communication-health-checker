from abc import ABC, abstractmethod
from typing import Any


class IPingEventPublisher(ABC):
    """定期 ping の結果イベントを配信する境界ポート。

    具象（InMemoryPingEventBus）は asyncio で実装され、FastAPI には依存しない。
    """

    @abstractmethod
    def publish(self, event: dict[str, Any]) -> None: ...
