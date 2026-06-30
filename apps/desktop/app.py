from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from apps.desktop.resources import resource_path
from apps.desktop.routers import ping, system, targets, ws
from communication_health_checker.application.services.periodic_ping_service import PeriodicPingService
from communication_health_checker.domain.models.core import (
    DomainException,
    EntityNotFoundException,
    InvalidOperationException,
    InvariantViolationException,
)
from communication_health_checker.modules import get_di_container

_STATUS_BY_EXCEPTION = {
    EntityNotFoundException: 404,
    InvalidOperationException: 400,
    InvariantViolationException: 409,
}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    get_di_container()  # DI を温める
    yield
    # 終了時: 稼働中の定期 ping を停止
    service = get_di_container().get(PeriodicPingService)
    await service.stop_all()


def _register_exception_handlers(app: FastAPI) -> None:
    async def domain_exception_handler(_: Request, exc: DomainException) -> JSONResponse:
        status = next(
            (s for t, s in _STATUS_BY_EXCEPTION.items() if isinstance(exc, t)),
            500,
        )
        return JSONResponse(status_code=status, content={"detail": str(exc)})

    async def validation_exception_handler(_: Request, exc: ValidationError) -> JSONResponse:
        # ドメイン VO（Host 等）の検証失敗を 422 に変換する
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)


def _mount_spa(app: FastAPI) -> None:
    static_dir = resource_path("statics")
    assets_dir = static_dir / "assets"
    index_file = static_dir / "index.html"

    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False, response_model=None)
    async def spa_fallback(full_path: str) -> FileResponse | PlainTextResponse:
        # API / WS の未マッチは JSON 404 を返したいのでフォールバックしない
        if full_path.startswith(("api/", "ws/")) or full_path == "ws":
            return PlainTextResponse("Not Found", status_code=404)
        if index_file.is_file():
            return FileResponse(index_file)
        return PlainTextResponse(
            "フロントエンド未ビルドです。../sample-gui-frontend で `npm run build` を実行してください。",
            status_code=200,
        )


def create_app() -> FastAPI:
    app = FastAPI(title="communication_health_checker", version="0.1.0", lifespan=lifespan)
    # main.py が uvicorn.Server を束ねる。未束縛（テスト等）では None。
    app.state.server = None

    # 1) API / WS ルーター（最優先で登録）
    app.include_router(targets.router)
    app.include_router(ping.router)
    app.include_router(system.router)
    app.include_router(ws.router)

    # 2) 例外ハンドラ
    _register_exception_handlers(app)

    # 3) 静的 SPA 配信 + catch-all（最後に登録）
    _mount_spa(app)

    return app
