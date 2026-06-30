from fastapi import APIRouter, Depends, Query

from communication_health_checker.application.dto.ping_dto import (
    OneShotRequest,
    PeriodicStartRequest,
    PingLogResponse,
    PingResultResponse,
    PingRunRequest,
    RepeatStartRequest,
    ScheduleStatusResponse,
)
from communication_health_checker.application.services.periodic_ping_service import PeriodicPingService
from communication_health_checker.application.use_cases.get_ping_logs_use_case import GetPingLogsUseCase
from communication_health_checker.application.use_cases.ping_targets_use_case import PingTargetsUseCase
from communication_health_checker.modules import get_di_container

router = APIRouter(prefix="/api/v1/ping", tags=["Ping"])


@router.post("/run", summary="ワンショット実行（1 回だけ送信）")
async def run_ping(
    request: OneShotRequest,
    use_case: PingTargetsUseCase = Depends(lambda: get_di_container().get(PingTargetsUseCase)),
) -> list[PingResultResponse]:
    # ワンショット = パラメータなしで 1 回だけ
    return use_case.execute(PingRunRequest(target_ids=request.target_ids, count=1, timeout_ms=request.timeout_ms))


@router.get("/logs/{target_id}", summary="ターゲット毎の ping ログ取得")
async def get_logs(
    target_id: str,
    limit: int = Query(default=200, ge=1, le=2000),
    use_case: GetPingLogsUseCase = Depends(lambda: get_di_container().get(GetPingLogsUseCase)),
) -> list[PingLogResponse]:
    return use_case.execute(target_id, limit=limit)


@router.post("/schedule/periodic", summary="定期実行開始（周期ごとに 1 回送信・停止まで継続）")
async def start_periodic(
    request: PeriodicStartRequest,
    service: PeriodicPingService = Depends(lambda: get_di_container().get(PeriodicPingService)),
) -> ScheduleStatusResponse:
    await service.start_periodic(request.target_ids, request.interval_sec, request.timeout_ms)
    return service.status()


@router.post("/schedule/repeat", summary="複数回実行開始（1 秒ごとに送信・指定回数で終了）")
async def start_repeat(
    request: RepeatStartRequest,
    service: PeriodicPingService = Depends(lambda: get_di_container().get(PeriodicPingService)),
) -> ScheduleStatusResponse:
    await service.start_repeat(request.target_ids, request.count, request.timeout_ms)
    return service.status()


@router.post("/schedule/stop", summary="スケジュール実行を停止（定期 / 複数回 共通）")
async def stop_schedule(
    service: PeriodicPingService = Depends(lambda: get_di_container().get(PeriodicPingService)),
) -> ScheduleStatusResponse:
    await service.stop()
    return service.status()


@router.get("/schedule/status", summary="スケジュール実行の状態取得")
async def schedule_status(
    service: PeriodicPingService = Depends(lambda: get_di_container().get(PeriodicPingService)),
) -> ScheduleStatusResponse:
    return service.status()
