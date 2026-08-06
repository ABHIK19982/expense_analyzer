"""Application configuration.

Secrets should be provided via environment variables in production.
Defaults match the previous Flask configs/keys.py placeholders.
"""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # MySQL metastore
    mysql_host: str = "expenseanalyzer.mysql.pythonanywhere-services.com"
    mysql_user: str = "expenseanalyzer"
    mysql_password: str = ""
    mysql_db: str = "expenseanalyzer$metastore"

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
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}/{self.mysql_db}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
