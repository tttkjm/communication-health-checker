from communication_health_checker.domain.repositories.i_ping_log_repository import IPingLogRepository
from communication_health_checker.domain.repositories.i_target_repository import ITargetRepository


class DeleteAllTargetsUseCase:
    """全ターゲットを削除する（ping ログも全削除）。"""

    def __init__(
        self,
        repository: ITargetRepository,
        ping_log_repository: IPingLogRepository,
    ) -> None:
        self._repository = repository
        self._ping_log_repository = ping_log_repository

    def execute(self) -> None:
        self._ping_log_repository.clear_all()
        self._repository.delete_all()
