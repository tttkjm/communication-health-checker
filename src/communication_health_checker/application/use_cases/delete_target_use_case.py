from communication_health_checker.domain.models.core import EntityNotFoundException
from communication_health_checker.domain.models.target.target_id import TargetId
from communication_health_checker.domain.repositories.i_ping_log_repository import IPingLogRepository
from communication_health_checker.domain.repositories.i_target_repository import ITargetRepository


class DeleteTargetUseCase:
    """ターゲットを削除する（関連 ping ログも併せて削除）。"""

    def __init__(
        self,
        repository: ITargetRepository,
        ping_log_repository: IPingLogRepository,
    ) -> None:
        self._repository = repository
        self._ping_log_repository = ping_log_repository

    def execute(self, target_id: str) -> None:
        tid = TargetId(value=target_id)
        if not self._repository.exists(tid):
            raise EntityNotFoundException(f"target not found: {target_id}")
        self._ping_log_repository.clear_by_target(tid)
        self._repository.delete(tid)
