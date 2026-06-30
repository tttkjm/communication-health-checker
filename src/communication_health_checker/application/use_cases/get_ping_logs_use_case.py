from communication_health_checker.application.converters import ping_log_to_response
from communication_health_checker.application.dto.ping_dto import PingLogResponse
from communication_health_checker.domain.models.core import EntityNotFoundException
from communication_health_checker.domain.models.target.target_id import TargetId
from communication_health_checker.domain.repositories.i_ping_log_repository import IPingLogRepository
from communication_health_checker.domain.repositories.i_target_repository import ITargetRepository


class GetPingLogsUseCase:
    """ターゲット毎の ping ログを取得する（新しい順）。"""

    def __init__(
        self,
        target_repository: ITargetRepository,
        ping_log_repository: IPingLogRepository,
    ) -> None:
        self._target_repository = target_repository
        self._ping_log_repository = ping_log_repository

    def execute(self, target_id: str, limit: int = 200) -> list[PingLogResponse]:
        tid = TargetId(value=target_id)
        if not self._target_repository.exists(tid):
            raise EntityNotFoundException(f"target not found: {target_id}")
        logs = self._ping_log_repository.find_by_target(tid, limit=limit)
        return [ping_log_to_response(log) for log in logs]
