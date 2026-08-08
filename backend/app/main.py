"""
Author: Abhik Pramanik
Change Date: 2026-08-07
Change details: Start uvicorn when main.py is executed so the FastAPI server
                listens on 127.0.0.1:8000 with reload enabled for local development.
FastAPI application entry point for Expense Analyzer.
Creates the ASGI app (middleware, routers, optional frontend static mount) and
exposes a ``__main__`` runner that starts uvicorn.
Inputs: environment / ``.env`` settings via ``get_settings()``; optional
        ``frontend/`` directory for static file serving.
Outputs: module-level ``app`` (FastAPI instance); when run as a script, a
         long-running uvicorn HTTP server on 127.0.0.1:8000.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import auth, expenses, reports
from app.services.mysql_backup import MySQLBackupWorker

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Purpose: Run startup/shutdown hooks for the FastAPI app (initialize DB and backup).
    Inputs: ``_app`` — the FastAPI application instance (unused beyond protocol).
    Outputs: async context manager that yields control for the app lifetime.
    """
    backup_worker = MySQLBackupWorker()
    try:
        init_db()
    except Exception as exc:  # noqa: BLE001
        # Allow the API to start even if SQLite init fails during local UI work.
        print(f"Warning: init_db failed: {exc}")
    await backup_worker.start()
    try:
        yield
    finally:
        await backup_worker.stop()


def create_app() -> FastAPI:
    """
    Purpose: Build and configure the Expense Analyzer FastAPI application.
    Inputs: None (reads settings via ``get_settings()``).
    Outputs: Configured ``FastAPI`` instance with session/CORS middleware,
             API routers, health endpoint, and optional frontend static mount.
    """
    settings = get_settings()
    app = FastAPI(
        title="Expense Analyzer",
        description="FastAPI backend for Expense Analyzer",
        version="2.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret_key,
        session_cookie=settings.session_cookie_name,
        max_age=settings.session_max_age_seconds,
        same_site=settings.session_same_site,
        https_only=settings.session_https_only,
    )

    origins = settings.cors_origin_list
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins != ["*"] else ["http://127.0.0.1:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    prefix = settings.api_prefix
    app.include_router(auth.router, prefix=prefix)
    app.include_router(expenses.router, prefix=prefix)
    app.include_router(reports.router, prefix=prefix)

    @app.get("/api/health")
    def health():
        """
        Purpose: Liveness check for the API process.
        Inputs: None.
        Outputs: JSON ``{"status": "ok"}``.
        """
        return {"status": "ok"}

    if FRONTEND_DIR.is_dir():
        app.mount(
            "/",
            StaticFiles(directory=str(FRONTEND_DIR), html=True),
            name="frontend",
        )

    return app


def run() -> None:
    """
    Purpose: Start the uvicorn ASGI server for local development.
    Inputs: None (host/port/reload are fixed for local use).
    Outputs: None; blocks while serving HTTP on 127.0.0.1:8000 with reload
             scoped to the ``app`` package directory only.
    """
    import uvicorn

    app_dir = Path(__file__).resolve().parent

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[str(app_dir)],
    )


app = create_app()


if __name__ == "__main__":
    run()
