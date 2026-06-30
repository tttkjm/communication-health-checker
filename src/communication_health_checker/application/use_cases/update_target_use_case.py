from communication_health_checker.application.converters import target_to_response
from communication_health_checker.application.dto.target_dto import TargetResponse, UpdateTargetRequest
from communication_health_checker.domain.models.core import EntityNotFoundException
from communication_health_checker.domain.models.target.host import Host
from communication_health_checker.domain.models.target.target_id import TargetId
from communication_health_checker.domain.ports.clock_port import ClockPort
from communication_health_checker.domain.repositories.i_target_repository import ITargetRepository


class UpdateTargetUseCase:
    """登録済みターゲットの情報を変更する。"""

    def __init__(self, repository: ITargetRepository, clock: ClockPort) -> None:
        self._repository = repository
        self._clock = clock

    def execute(self, target_id: str, request: UpdateTargetRequest) -> TargetResponse:
        tid = TargetId(value=target_id)
        target = self._repository.find_by_id(tid)
        if target is None:
            raise EntityNotFoundException(f"target not found: {target_id}")
        target.rename(request.name)
        target.change_host(Host(value=request.host))
        target.description = request.description
        target.updated_at = self._clock.now()
        target.validate_invariants()
        self._repository.save(target)
        return target_to_response(target)
