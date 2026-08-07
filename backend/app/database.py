"""
Author: Abhik Pramanik
Change Date: 2026-08-07
Change details: Switch primary database engine from MySQL to local SQLite file storage.
SQLAlchemy engine and session management for the Expense Analyzer metastore.
Inputs: settings from ``get_settings()`` (SQLite file path).
Outputs: SQLAlchemy ``engine``, ``SessionLocal``, ``get_db()`` generator, ``init_db()``.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
settings.sqlite_db_file.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.sqlalchemy_database_uri,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Purpose: Provide a SQLAlchemy session per request for FastAPI dependency injection.
    Inputs: None (uses module-level ``SessionLocal`` bound to SQLite).
    Outputs: Yields a ``Session``; closes it when the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Purpose: Create metastore tables in SQLite if they do not exist.
    Inputs: None (uses ``Base.metadata`` and the SQLite ``engine``).
    Outputs: None; creates ``user_details`` and any other registered models.
    """
    from app.models import user  # noqa: F401

    Base.metadata.create_all(bind=engine)
