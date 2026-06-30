import asyncio

from communication_health_checker.application.dto.target_dto import CreateTargetRequest
from communication_health_checker.application.services.periodic_ping_service import PeriodicPingService
from communication_health_checker.application.use_cases.create_target_use_case import CreateTargetUseCase
from communication_health_checker.application.use_cases.ping_targets_use_case import PingTargetsUseCase
from tests.unit.fakes import (
    FakePingPort,
    FixedClock,
    InMemoryPingLogRepository,
    InMemoryTargetRepository,
    RecordingPublisher,
)


def _build_service() -> tuple[PeriodicPingService, RecordingPublisher, FakePingPort]:
    target_repo = InMemoryTargetRepository()
    log_repo = InMemoryPingLogRepository()
    CreateTargetUseCase(target_repo, FixedClock()).execute(CreateTargetRequest(name="R1", host="127.0.0.1"))
    ping_port = FakePingPort()
    ping_uc = PingTargetsUseCase(target_repo, log_repo, ping_port, FixedClock())
    publisher = RecordingPublisher()
    return PeriodicPingService(ping_uc, publisher), publisher, ping_port


async def _periodic_scenario() -> tuple[RecordingPublisher, PeriodicPingService]:
    service, publisher, _ = _build_service()
    assert service.status().running is False

    await service.start_periodic(target_ids=None, interval_sec=1, timeout_ms=500)
    assert service.status().running is True
    assert service.status().mode == "periodic"

    for _ in range(50):  # 1 サイクル分の ping_result を待つ
        if any(e["type"] == "ping_result" for e in publisher.events):
            break
        await asyncio.sleep(0.05)

    await service.stop()
    assert service.status().running is False
    return publisher, service


async def _repeat_scenario() -> RecordingPublisher:
    service, publisher, ping_port = _build_service()
    # 1 秒間隔だと遅いので、複数回モードの「指定回数で終了」を検証するために count=3
    await service.start_repeat(target_ids=None, count=3, timeout_ms=200)

    for _ in range(200):  # 自動終了（running=False）まで待つ（最大 ~10s）
        if not service.status().running:
            break
        await asyncio.sleep(0.05)

    assert service.status().running is False
    # 3 回ぶん送信されている（FakePingPort 呼び出し回数 = サイクル数）
    assert len(ping_port.calls) == 3
    return publisher


def test_periodic_runs_and_stops() -> None:
    publisher, _ = asyncio.run(_periodic_scenario())
    types = [e["type"] for e in publisher.events]
    assert "schedule_status" in types
    assert "ping_result" in types


def test_repeat_auto_stops_after_count() -> None:
    publisher = asyncio.run(_repeat_scenario())
    ping_results = [e for e in publisher.events if e["type"] == "ping_result"]
    assert len(ping_results) == 3  # 1 ターゲット × 3 サイクル
    # 最後に running=False の状態が配信される
    last_status = [e for e in publisher.events if e["type"] == "schedule_status"][-1]
    assert last_status["running"] is False
