from communication_health_checker.application.converters import target_to_response
from communication_health_checker.application.dto.target_dto import TargetResponse
from communication_health_checker.domain.repositories.i_target_repository import ITargetRepository


class ListTargetsUseCase:
    """ターゲットを一覧取得する。"""

    def __init__(self, repository: ITargetRepository) -> None:
        self._repository = repository

    def execute(self) -> list[TargetResponse]:
        return [target_to_response(t) for t in self._repository.find_all()]
