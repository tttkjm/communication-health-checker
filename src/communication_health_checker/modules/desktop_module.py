import os

from injector import Injector, Module, provider, singleton

from communication_health_checker.application.services.periodic_ping_service import PeriodicPingService
from communication_health_checker.application.use_cases.create_target_use_case import CreateTargetUseCase
from communication_health_checker.application.use_cases.delete_all_targets_use_case import DeleteAllTargetsUseCase
from communication_health_checker.application.use_cases.delete_target_use_case import DeleteTargetUseCase
from communication_health_checker.application.use_cases.get_ping_logs_use_case import GetPingLogsUseCase
from communication_health_checker.application.use_cases.get_target_use_case import GetTargetUseCase
from communication_health_checker.application.use_cases.list_targets_use_case import ListTargetsUseCase
from communication_health_checker.application.use_cases.ping_targets_use_case import PingTargetsUseCase
from communication_health_checker.application.use_cases.update_target_use_case import UpdateTargetUseCase
from communication_health_checker.domain.ports.clock_port import ClockPort
from communication_health_checker.domain.ports.ping_event_publisher import IPingEventPublisher
from communication_health_checker.domain.ports.ping_port import PingPort
from communication_health_checker.domain.repositories.i_ping_log_repository import IPingLogRepository
from communication_health_checker.domain.repositories.i_target_repository import ITargetRepository
from communication_health_checker.infrastructure.adapters.in_memory_ping_event_bus import InMemoryPingEventBus
from communication_health_checker.infrastructure.adapters.subprocess_ping_adapter import SubprocessPingAdapter
from communication_health_checker.infrastructure.adapters.system_clock import SystemClock
from communication_health_checker.infrastructure.repositories.sqlite.connection import Database
from communication_health_checker.infrastructure.repositories.sqlite.ping_log_repository import SqlitePingLogRepository
from communication_health_checker.infrastructure.repositories.sqlite.target_repository import SqliteTargetRepository


class DesktopModule(Module):
    """デスクトップ環境用 DI モジュール（SQLite + subprocess ping + インメモリイベントバス）。"""

    _instance: Injector | None = None

    @classmethod
    def get_instance(cls) -> Injector:
        if cls._instance is None:
            cls._instance = Injector([cls()])
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """テスト用: シングルトンを破棄する。"""
        cls._instance = None

    # --- infrastructure ---------------------------------------------------
    @singleton
    @provider
    def database(self) -> Database:
        return Database(os.getenv("SQLITE_DB_PATH", "communication_health_checker.db"))

    @singleton
    @provider
    def target_repository(self, database: Database) -> ITargetRepository:
        return SqliteTargetRepository(database)

    @singleton
    @provider
    def ping_log_repository(self, database: Database) -> IPingLogRepository:
        return SqlitePingLogRepository(database)

    @singleton
    @provider
    def clock(self) -> ClockPort:
        return SystemClock()

    @singleton
    @provider
    def ping_port(self) -> PingPort:
        return SubprocessPingAdapter()

    @singleton
    @provider
    def event_bus(self) -> InMemoryPingEventBus:
        return InMemoryPingEventBus()

    @singleton
    @provider
    def publisher(self, bus: InMemoryPingEventBus) -> IPingEventPublisher:
        return bus

    # --- use cases (target CRUD) -----------------------------------------
    @singleton
    @provider
    def create_target_use_case(self, repo: ITargetRepository, clock: ClockPort) -> CreateTargetUseCase:
        return CreateTargetUseCase(repo, clock)

    @singleton
    @provider
    def update_target_use_case(self, repo: ITargetRepository, clock: ClockPort) -> UpdateTargetUseCase:
        return UpdateTargetUseCase(repo, clock)

    @singleton
    @provider
    def get_target_use_case(self, repo: ITargetRepository) -> GetTargetUseCase:
        return GetTargetUseCase(repo)

    @singleton
    @provider
    def list_targets_use_case(self, repo: ITargetRepository) -> ListTargetsUseCase:
        return ListTargetsUseCase(repo)

    @singleton
    @provider
    def delete_target_use_case(self, repo: ITargetRepository, log_repo: IPingLogRepository) -> DeleteTargetUseCase:
        return DeleteTargetUseCase(repo, log_repo)

    @singleton
    @provider
    def delete_all_targets_use_case(
        self, repo: ITargetRepository, log_repo: IPingLogRepository
    ) -> DeleteAllTargetsUseCase:
        return DeleteAllTargetsUseCase(repo, log_repo)

    # --- use cases (ping) -------------------------------------------------
    @singleton
    @provider
    def ping_targets_use_case(
        self,
        repo: ITargetRepository,
        log_repo: IPingLogRepository,
        ping_port: PingPort,
        clock: ClockPort,
    ) -> PingTargetsUseCase:
        return PingTargetsUseCase(repo, log_repo, ping_port, clock)

    @singleton
    @provider
    def get_ping_logs_use_case(self, repo: ITargetRepository, log_repo: IPingLogRepository) -> GetPingLogsUseCase:
        return GetPingLogsUseCase(repo, log_repo)

    # --- application service (periodic) ----------------------------------
    @singleton
    @provider
    def periodic_ping_service(self, ping_uc: PingTargetsUseCase, publisher: IPingEventPublisher) -> PeriodicPingService:
        return PeriodicPingService(ping_uc, publisher)
