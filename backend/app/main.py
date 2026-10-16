"""Ponto de entrada da API: `uvicorn app.main:app`."""

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.core.config import get_settings
from app.core.errors import error_body, register_exception_handlers
from app.core.logging import RequestContextMiddleware, configure_logging
from app.db.session import get_sessionmaker
from app.modules.accounts.router import router as accounts_router
from app.modules.auth.router import router as auth_router
from app.modules.catalog.router import router as catalog_router
from app.modules.inventory.router import router as inventory_router
from app.modules.orders.router import router as orders_router
from app.modules.reports.router import router as reports_router
from app.modules.staff.router import router as staff_router

API_DESCRIPTION = """
API do **Cali Burger**: cardápio com disponibilidade pelo estoque, pedidos com baixa
transacional de ingredientes, fila da cozinha, estoque, relatórios e equipe.

**Autenticação**: `POST /api/v1/auth/login` cria uma sessão em cookie HttpOnly. Requisições
que alteram dados precisam do cabeçalho `X-CSRF-Token` com o valor do cookie `cb_csrf`.
"""


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="Cali Burger API",
        version="1.0.0",
        description=API_DESCRIPTION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    register_exception_handlers(app)

    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["Content-Type", "X-CSRF-Token", "Idempotency-Key"],
        )
    app.add_middleware(RequestContextMiddleware)

    api = APIRouter(prefix="/api/v1")
    for router in (
        auth_router,
        accounts_router,
        catalog_router,
        inventory_router,
        orders_router,
        reports_router,
        staff_router,
    ):
        api.include_router(router)
    app.include_router(api)

    @app.get("/api/health", tags=["Saúde"], summary="Verifica a API e o banco")
    def health() -> JSONResponse:
        try:
            with get_sessionmaker()() as db:
                db.execute(text("SELECT 1"))
        except Exception:
            return JSONResponse(
                error_body("database_unavailable", "Banco de dados indisponível."),
                status_code=503,
            )
        return JSONResponse({"status": "ok", "database": "ok"})

    settings.menu_media_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=settings.media_dir), name="media")
    return app


app = create_app()
