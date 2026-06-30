import asyncio

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/system", tags=["System"])

_SHUTDOWN_DELAY_SEC = 0.3


class ShutdownResponse(BaseModel):
    shutting_down: bool = Field(..., description="サーバ終了処理を開始したか")
    detail: str = Field(default="", description="補足")


class HealthResponse(BaseModel):
    app: str = Field(..., description="アプリ識別子")
    status: str = Field(..., description="状態")


@router.get("/health", summary="ヘルスチェック（シングルインスタンス判定にも使用）")
async def health() -> HealthResponse:
    return HealthResponse(app="communication_health_checker", status="ok")


@router.post("/shutdown", summary="バックエンドサーバを正常終了する")
async def shutdown(request: Request) -> ShutdownResponse:
    """uvicorn サーバへ終了を要求する。

    レスポンスを返してから should_exit を立てることで、HTTP 応答が
    確実にクライアントへ届いた後に graceful shutdown（lifespan 終了→
    定期 ping 停止）が走るようにする。
    """
    server = getattr(request.app.state, "server", None)
    if server is None:
        # TestClient / 開発時などサーバ未登録
        return ShutdownResponse(shutting_down=False, detail="no server bound")

    async def _delayed_stop() -> None:
        await asyncio.sleep(_SHUTDOWN_DELAY_SEC)
        server.should_exit = True

    asyncio.create_task(_delayed_stop())
    return ShutdownResponse(shutting_down=True, detail="server will stop shortly")
