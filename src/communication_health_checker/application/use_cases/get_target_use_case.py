from communication_health_checker.application.converters import target_to_response
from communication_health_checker.application.dto.target_dto import TargetResponse
from communication_health_checker.domain.models.core import EntityNotFoundException
from communication_health_checker.domain.models.target.target_id import TargetId
from communication_health_checker.domain.repositories.i_target_repository import ITargetRepository


class GetTargetUseCase:
    """ターゲットを 1 件取得する。"""

    def __init__(self, repository: ITargetRepository) -> None:
        self._repository = repository

    def execute(self, target_id: str) -> TargetResponse:
        target = self._repository.find_by_id(TargetId(value=target_id))
        if target is None:
            raise EntityNotFoundException(f"target not found: {target_id}")
        return target_to_response(target)
