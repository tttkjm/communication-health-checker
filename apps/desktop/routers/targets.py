from fastapi import APIRouter, Depends

from communication_health_checker.application.dto.target_dto import (
    CreateTargetRequest,
    TargetResponse,
    UpdateTargetRequest,
)
from communication_health_checker.application.use_cases.create_target_use_case import CreateTargetUseCase
from communication_health_checker.application.use_cases.delete_all_targets_use_case import DeleteAllTargetsUseCase
from communication_health_checker.application.use_cases.delete_target_use_case import DeleteTargetUseCase
from communication_health_checker.application.use_cases.get_target_use_case import GetTargetUseCase
from communication_health_checker.application.use_cases.list_targets_use_case import ListTargetsUseCase
from communication_health_checker.application.use_cases.update_target_use_case import UpdateTargetUseCase
from communication_health_checker.modules import get_di_container

router = APIRouter(prefix="/api/v1/targets", tags=["Targets"])


@router.post("", status_code=201, summary="ターゲット登録")
async def create_target(
    request: CreateTargetRequest,
    use_case: CreateTargetUseCase = Depends(lambda: get_di_container().get(CreateTargetUseCase)),
) -> TargetResponse:
    return use_case.execute(request)


@router.get("", summary="ターゲット一覧取得")
async def list_targets(
    use_case: ListTargetsUseCase = Depends(lambda: get_di_container().get(ListTargetsUseCase)),
) -> list[TargetResponse]:
    return use_case.execute()


@router.get("/{target_id}", summary="ターゲット取得")
async def get_target(
    target_id: str,
    use_case: GetTargetUseCase = Depends(lambda: get_di_container().get(GetTargetUseCase)),
) -> TargetResponse:
    return use_case.execute(target_id)


@router.put("/{target_id}", summary="ターゲット更新")
async def update_target(
    target_id: str,
    request: UpdateTargetRequest,
    use_case: UpdateTargetUseCase = Depends(lambda: get_di_container().get(UpdateTargetUseCase)),
) -> TargetResponse:
    return use_case.execute(target_id, request)


@router.delete("/{target_id}", status_code=204, summary="ターゲット削除")
async def delete_target(
    target_id: str,
    use_case: DeleteTargetUseCase = Depends(lambda: get_di_container().get(DeleteTargetUseCase)),
) -> None:
    use_case.execute(target_id)


@router.delete("", status_code=204, summary="ターゲット全削除")
async def delete_all_targets(
    use_case: DeleteAllTargetsUseCase = Depends(lambda: get_di_container().get(DeleteAllTargetsUseCase)),
) -> None:
    use_case.execute()
