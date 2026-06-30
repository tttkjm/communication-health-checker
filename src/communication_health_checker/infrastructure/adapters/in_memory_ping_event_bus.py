import asyncio
from typing import Any

from communication_health_checker.domain.ports.ping_event_publisher import IPingEventPublisher

_QUEUE_MAXSIZE = 1000


class InMemoryPingEventBus(IPingEventPublisher):
    """asyncio ベースのインメモリ pub/sub。

    - publish(): イベントを全 subscriber のキューへ非ブロッキング投入（イベントループスレッドから呼ぶ）
    - subscribe()/unsubscribe(): presentation 層（WebSocket）が購読に使う

    FastAPI に依存しないため infrastructure 層に置ける。
    """

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()

    def subscribe(self) -> "asyncio.Queue[dict[str, Any]]":
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=_QUEUE_MAXSIZE)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: "asyncio.Queue[dict[str, Any]]") -> None:
        self._subscribers.discard(queue)

    def publish(self, event: dict[str, Any]) -> None:
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # 詰まっている購読者はスキップ（最新性優先）
                pass
