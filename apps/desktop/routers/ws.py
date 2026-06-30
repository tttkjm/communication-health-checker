import asyncio
import contextlib

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from communication_health_checker.application.services.periodic_ping_service import PeriodicPingService
from communication_health_checker.infrastructure.adapters.in_memory_ping_event_bus import InMemoryPingEventBus
from communication_health_checker.modules import get_di_container

router = APIRouter()


@router.websocket("/ws/ping")
async def ws_ping(websocket: WebSocket) -> None:
    """定期 ping の結果イベントをクライアントへストリームする。"""
    await websocket.accept()
    container = get_di_container()
    bus: InMemoryPingEventBus = container.get(InMemoryPingEventBus)
    service: PeriodicPingService = container.get(PeriodicPingService)

    queue = bus.subscribe()
    # 接続直後に現在のスケジュール状態を送る
    await websocket.send_json({"type": "schedule_status", **service.status().model_dump()})

    recv_task = asyncio.create_task(websocket.receive_text())
    get_task = asyncio.create_task(queue.get())
    try:
        while True:
            done, _ = await asyncio.wait({recv_task, get_task}, return_when=asyncio.FIRST_COMPLETED)
            if recv_task in done:
                # クライアントからのメッセージ or 切断検知
                recv_task.result()
                recv_task = asyncio.create_task(websocket.receive_text())
            if get_task in done:
                event = get_task.result()
                await websocket.send_json(event)
                get_task = asyncio.create_task(queue.get())
    except WebSocketDisconnect:
        pass
    finally:
        bus.unsubscribe(queue)
        for task in (recv_task, get_task):
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task
