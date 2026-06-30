"""テスト用のインメモリ／フェイク実装。"""

from datetime import UTC, datetime
from typing import Any

from communication_health_checker.domain.models.ping.ping_log import PingLog
from communication_health_checker.domain.models.ping.ping_probe import PingProbe
from communication_health_checker.domain.models.target.target import Target
from communication_health_checker.domain.models.target.target_id import TargetId
from communication_health_checker.domain.ports.clock_port import ClockPort
from communication_health_checker.domain.ports.ping_event_publisher import IPingEventPublisher
from communication_health_checker.domain.ports.ping_port import PingPort
from communication_health_checker.domain.repositories.i_ping_log_repository import IPingLogRepository
from communication_health_checker.domain.repositories.i_target_repository import ITargetRepository


class InMemoryTargetRepository(ITargetRepository):
    def __init__(self) -> None:
        self._store: dict[str, Target] = {}

    def save(self, target: Target) -> None:
        self._store[str(target.target_id)] = target

    def find_by_id(self, target_id: TargetId) -> Target | None:
        return self._store.get(str(target_id))

    def find_all(self) -> list[Target]:
        return list(self._store.values())

    def exists(self, target_id: TargetId) -> bool:
        return str(target_id) in self._store

    def delete(self, target_id: TargetId) -> None:
        self._store.pop(str(target_id), None)

    def delete_all(self) -> None:
        self._store.clear()


class InMemoryPingLogRepository(IPingLogRepository):
    def __init__(self) -> None:
        self._logs: list[PingLog] = []

    def append_many(self, logs: list[PingLog]) -> None:
        self._logs.extend(logs)

    def find_by_target(self, target_id: TargetId, limit: int = 200) -> list[PingLog]:
        items = [log for log in self._logs if str(log.target_id) == str(target_id)]
        return list(reversed(items))[:limit]

    def clear_by_target(self, target_id: TargetId) -> None:
        self._logs = [log for log in self._logs if str(log.target_id) != str(target_id)]

    def clear_all(self) -> None:
        self._logs.clear()


class FakePingPort(PingPort):
    """常に「最初の 1 回成功・残り失敗」を返すフェイク。"""

    def __init__(self) -> None:
        self.calls: list[tuple[str, int, int]] = []

    def ping_once(self, host: str, count: int, timeout_ms: int) -> list[PingProbe]:
        self.calls.append((host, count, timeout_ms))
        return [
            PingProbe(
                seq=i + 1,
                success=(i == 0),
                rtt_ms=1.5 if i == 0 else None,
                ttl=64 if i == 0 else None,
                error=None if i == 0 else "timeout",
            )
            for i in range(count)
        ]


class FixedClock(ClockPort):
    def now(self) -> datetime:
        return datetime(2026, 1, 1, tzinfo=UTC)


class RecordingPublisher(IPingEventPublisher):
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def publish(self, event: dict[str, Any]) -> None:
        self.events.append(event)
