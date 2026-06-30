import pytest

from communication_health_checker.application.dto.ping_dto import PingRunRequest
from communication_health_checker.application.dto.target_dto import CreateTargetRequest, UpdateTargetRequest
from communication_health_checker.application.use_cases.create_target_use_case import CreateTargetUseCase
from communication_health_checker.application.use_cases.delete_all_targets_use_case import DeleteAllTargetsUseCase
from communication_health_checker.application.use_cases.delete_target_use_case import DeleteTargetUseCase
from communication_health_checker.application.use_cases.get_target_use_case import GetTargetUseCase
from communication_health_checker.application.use_cases.list_targets_use_case import ListTargetsUseCase
from communication_health_checker.application.use_cases.ping_targets_use_case import PingTargetsUseCase
from communication_health_checker.application.use_cases.update_target_use_case import UpdateTargetUseCase
from communication_health_checker.domain.models.core import EntityNotFoundException
from communication_health_checker.domain.models.target.target_id import TargetId
from tests.unit.fakes import (
    FakePingPort,
    FixedClock,
    InMemoryPingLogRepository,
    InMemoryTargetRepository,
)


@pytest.fixture
def repos():
    return InMemoryTargetRepository(), InMemoryPingLogRepository()


def test_create_and_get_target(repos):
    target_repo, _ = repos
    created = CreateTargetUseCase(target_repo, FixedClock()).execute(
        CreateTargetRequest(name="R1", host="192.168.0.1", description="x")
    )
    fetched = GetTargetUseCase(target_repo).execute(created.id)
    assert fetched.name == "R1"
    assert fetched.host == "192.168.0.1"


def test_update_target(repos):
    target_repo, _ = repos
    created = CreateTargetUseCase(target_repo, FixedClock()).execute(CreateTargetRequest(name="R1", host="192.168.0.1"))
    updated = UpdateTargetUseCase(target_repo, FixedClock()).execute(
        created.id, UpdateTargetRequest(name="R2", host="10.0.0.1", description="y")
    )
    assert updated.name == "R2"
    assert updated.host == "10.0.0.1"


def test_update_missing_raises(repos):
    target_repo, _ = repos
    with pytest.raises(EntityNotFoundException):
        UpdateTargetUseCase(target_repo, FixedClock()).execute(
            "tgt_00000000000000000000000000000000",
            UpdateTargetRequest(name="x", host="127.0.0.1"),
        )


def test_delete_and_delete_all(repos):
    target_repo, log_repo = repos
    create = CreateTargetUseCase(target_repo, FixedClock())
    a = create.execute(CreateTargetRequest(name="A", host="127.0.0.1"))
    create.execute(CreateTargetRequest(name="B", host="127.0.0.2"))
    DeleteTargetUseCase(target_repo, log_repo).execute(a.id)
    assert len(ListTargetsUseCase(target_repo).execute()) == 1
    DeleteAllTargetsUseCase(target_repo, log_repo).execute()
    assert ListTargetsUseCase(target_repo).execute() == []


def test_ping_targets_aggregates_and_persists(repos):
    target_repo, log_repo = repos
    created = CreateTargetUseCase(target_repo, FixedClock()).execute(CreateTargetRequest(name="R1", host="127.0.0.1"))
    uc = PingTargetsUseCase(target_repo, log_repo, FakePingPort(), FixedClock())
    results = uc.execute(PingRunRequest(target_ids=[created.id], count=4))
    assert len(results) == 1
    r = results[0]
    assert r.packets_sent == 4
    assert r.packets_received == 1  # FakePingPort: 1 成功
    assert r.packets_lost == 3
    assert r.loss_pct == 75.0
    assert r.rtt_avg_ms == 1.5
    # ログが 4 件保存される
    assert len(log_repo.find_by_target(TargetId(value=created.id))) == 4


def test_ping_all_when_no_ids(repos):
    target_repo, log_repo = repos
    create = CreateTargetUseCase(target_repo, FixedClock())
    create.execute(CreateTargetRequest(name="A", host="127.0.0.1"))
    create.execute(CreateTargetRequest(name="B", host="127.0.0.2"))
    uc = PingTargetsUseCase(target_repo, log_repo, FakePingPort(), FixedClock())
    results = uc.execute(PingRunRequest(target_ids=None, count=2))
    assert len(results) == 2
