"""
Stratum AI — API entrypoint + web frontend server.

Run:  uvicorn CORE_AGENT_INFRASTRUCTURE.api.main:app --host 0.0.0.0 --port 8000
"""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from CORE_AGENT_INFRASTRUCTURE.config import resolve_config
from CORE_AGENT_INFRASTRUCTURE.db.session import init_db

logger = logging.getLogger("stratum.api")

WEB_DIR = Path(__file__).resolve().parents[2] / "web"


def create_app() -> FastAPI:
    cfg = resolve_config()

    logging.basicConfig(level=cfg.log_level)
    from CORE_AGENT_INFRASTRUCTURE.api.logging_monitoring import setup_logging
    setup_logging(level=cfg.log_level)

    init_db()

    app = FastAPI(
        title="Stratum AI",
        version="1.0.0",
        description="Stratum AI operations platform — Stratum Care, Stratum Realty, Stratum Freight. Built by kingscottishDEV · N.A.S — Nexus Audit Security",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from CORE_AGENT_INFRASTRUCTURE.api.routers import (agents, audit, auth, clients,
                                                       demo, support, system, users)

    for router in (auth.router, system.router, clients.router, agents.router,
                   support.router, audit.router, users.router, demo.router):
        app.include_router(router, prefix=cfg.api_prefix)

    @app.get("/healthz", include_in_schema=False)
    def healthz():
        return {"status": "ok", "service": "Stratum AI", "demo_mode": cfg.is_demo()}

    # --- static web frontend ---------------------------------------------------
    if WEB_DIR.exists():
        app.mount("/assets", StaticFiles(directory=str(WEB_DIR / "assets")), name="assets")

        @app.get("/", include_in_schema=False)
        def index():
            return FileResponse(str(WEB_DIR / "index.html"))

        @app.get("/{path:path}", include_in_schema=False)
        def spa_fallback(path: str):
            # serve the SPA for any non-API route (client-side routing)
            candidate = WEB_DIR / path
            if candidate.is_file():
                return FileResponse(str(candidate))
            return FileResponse(str(WEB_DIR / "index.html"))

    return app


app = create_app()
