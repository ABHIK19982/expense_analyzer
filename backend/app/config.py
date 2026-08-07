"""
Author: Abhik Pramanik
Change Date: 2026-08-07
Change details: Replace MySQL metastore settings with local SQLite file path.
Application configuration for Expense Analyzer.
Secrets should be provided via environment variables in production.
Inputs: environment variables and optional ``.env`` file in the backend directory.
Outputs: ``Settings`` instance via ``get_settings()`` with database URI and app options.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # SQLite metastore (primary user/password storage)
    sqlite_db_path: str = "data/metastore.db"

    # AWS DynamoDB
    aws_access_key: str = ""
    aws_secret_key: str = ""
    db_region: str = "ap-south-1"
    table_name: str = "expense_table"

    # Auth / password policy
    pass_expiry: int = 30
    max_pass_history: int = 3

    # Signed session cookie (replaces Flask-Login session)
    session_secret_key: str = os.environ.get(
        "SESSION_SECRET_KEY",
        "dev-session-secret-change-me",
    )
    session_max_age_seconds: int = 60 * 60 * 24  # 1 day
    session_cookie_name: str = "expense_session"
    session_https_only: bool = False
    session_same_site: str = "lax"

    # API
    api_prefix: str = "/api"
    cors_origins: str = "http://127.0.0.1:8000,http://localhost:8000"

    # Graph category groupings (preserved from Flask app)
    graph1_comm_types: list[str] = ["Bills", "Rents", "Transportation", "Others"]
    graph2_comm_types: list[str] = [
        "Grocery",
        "Green-Grocery",
        "Food",
        "Entertainment",
        "Clothes",
        "Miscellaneous",
    ]

    @property
    def sqlalchemy_database_uri(self) -> str:
        """
        Purpose: Build the SQLAlchemy connection URI for the local SQLite metastore.
        Inputs: ``sqlite_db_path`` setting (resolved to an absolute path).
        Outputs: SQLite URI string, e.g. ``sqlite:////abs/path/to/metastore.db``.
        """
        path = Path(self.sqlite_db_path).resolve()
        return f"sqlite:///{path}"

    @property
    def sqlite_db_file(self) -> Path:
        """
        Purpose: Return the resolved filesystem path to the SQLite database file.
        Inputs: ``sqlite_db_path`` setting.
        Outputs: Absolute ``Path`` to the SQLite database file.
        """
        return Path(self.sqlite_db_path).resolve()

    @property
    def cors_origin_list(self) -> list[str]:
        """
        Purpose: Parse comma-separated CORS origins into a list.
        Inputs: ``cors_origins`` setting string.
        Outputs: List of origin URL strings.
        """
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """
    Purpose: Return a cached singleton ``Settings`` instance.
    Inputs: None (reads from environment / ``.env``).
    Outputs: ``Settings`` instance.
    """
    return Settings()
