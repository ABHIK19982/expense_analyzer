"""FastAPI application entry point."""

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

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        init_db()
    except Exception as exc:  # noqa: BLE001
        # Allow the API to start even if MySQL is unreachable during local UI work.
        print(f"Warning: init_db failed: {exc}")
    yield


def create_app() -> FastAPI:
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
        return {"status": "ok"}

    if FRONTEND_DIR.is_dir():
        app.mount(
            "/",
            StaticFiles(directory=str(FRONTEND_DIR), html=True),
            name="frontend",
        )

    return app


app = create_app()
