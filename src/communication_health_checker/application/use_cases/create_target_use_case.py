from communication_health_checker.application.converters import target_to_response
from communication_health_checker.application.dto.target_dto import CreateTargetRequest, TargetResponse
from communication_health_checker.domain.models.target.host import Host
from communication_health_checker.domain.models.target.target import Target
from communication_health_checker.domain.models.target.target_id import TargetId
from communication_health_checker.domain.ports.clock_port import ClockPort
from communication_health_checker.domain.repositories.i_target_repository import ITargetRepository


class CreateTargetUseCase:
    """ターゲット機器を登録する。"""

    def __init__(self, repository: ITargetRepository, clock: ClockPort) -> None:
        self._repository = repository
        self._clock = clock

    def execute(self, request: CreateTargetRequest) -> TargetResponse:
        now = self._clock.now()
        target = Target(
            target_id=TargetId.generate(),
            name=request.name,
            host=Host(value=request.host),
            description=request.description,
            created_at=now,
            updated_at=now,
        )
        target.validate_invariants()
        self._repository.save(target)
        return target_to_response(target)
