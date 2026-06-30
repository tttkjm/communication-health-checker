import asyncio
import contextlib

from communication_health_checker.application.dto.ping_dto import PingRunRequest, ScheduleStatusResponse
from communication_health_checker.application.use_cases.ping_targets_use_case import PingTargetsUseCase
from communication_health_checker.domain.ports.ping_event_publisher import IPingEventPublisher

_REPEAT_INTERVAL_SEC = 1.0


class PeriodicPingService:
    """バックエンド駆動のスケジュール ping を司るステートフルなアプリケーションサービス。

    2 つのモードを単一の asyncio タスクで実現する（同時に 1 つだけ稼働）:

    - periodic: 周期ごとに 1 回送信し、停止されるまで継続（max_cycles=None）
    - repeat:   1 秒ごとに 1 回送信し、指定回数（max_cycles）に達したら自動終了

    各サイクルは 1 回の送信（count=1）。結果は publisher で配信する。
    単一インスタンス（DI で singleton）として扱う。
    """

    def __init__(self, ping_targets_use_case: PingTargetsUseCase, publisher: IPingEventPublisher) -> None:
        self._uc = ping_targets_use_case
        self._publisher = publisher
        self._task: asyncio.Task | None = None
        self._running = False
        self._mode: str | None = None
        self._interval_sec: float = _REPEAT_INTERVAL_SEC
        self._target_ids: list[str] | None = None
        self._max_cycles: int | None = None
        self._completed = 0
        self._timeout_ms = 1000

    def status(self) -> ScheduleStatusResponse:
        running = self._running
        return ScheduleStatusResponse(
            running=running,
            mode=self._mode if running else None,
            interval_sec=self._interval_sec if running else None,
            target_ids=self._target_ids if running else None,
            total_count=self._max_cycles if running else None,
            completed_cycles=self._completed if running else 0,
        )

    async def start_periodic(self, target_ids: list[str] | None, interval_sec: float, timeout_ms: int) -> None:
        """周期ごとに 1 回送信し続ける（停止するまで）。"""
        await self._start(target_ids, interval_sec, None, timeout_ms, mode="periodic")

    async def start_repeat(self, target_ids: list[str] | None, count: int, timeout_ms: int) -> None:
        """1 秒ごとに送信し、count 回で自動終了する。"""
        await self._start(target_ids, _REPEAT_INTERVAL_SEC, count, timeout_ms, mode="repeat")

    async def stop(self) -> None:
        if self._task is not None and not self._task.done():
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        self._task = None
        self._running = False

    async def stop_all(self) -> None:
        await self.stop()

    async def _start(
        self,
        target_ids: list[str] | None,
        interval_sec: float,
        max_cycles: int | None,
        timeout_ms: int,
        mode: str,
    ) -> None:
        await self.stop()
        self._target_ids = target_ids
        self._interval_sec = interval_sec
        self._max_cycles = max_cycles
        self._timeout_ms = timeout_ms
        self._mode = mode
        self._completed = 0
        self._running = True
        self._task = asyncio.create_task(self._loop())
        self._publish_status()

    async def _loop(self) -> None:
        request = PingRunRequest(target_ids=self._target_ids, count=1, timeout_ms=self._timeout_ms)
        try:
            while True:
                # blocking な subprocess 実行はスレッドへ逃がす
                results = await asyncio.to_thread(self._uc.execute, request)
                for result in results:
                    self._publisher.publish({"type": "ping_result", "result": result.model_dump()})
                self._completed += 1
                if self._max_cycles is not None and self._completed >= self._max_cycles:
                    break  # 複数回モード: 指定回数で終了
                await asyncio.sleep(self._interval_sec)
        finally:
            # 自然終了・キャンセルのいずれでも停止状態を通知する
            self._running = False
            self._publish_status()

    def _publish_status(self) -> None:
        self._publisher.publish({"type": "schedule_status", **self.status().model_dump()})
