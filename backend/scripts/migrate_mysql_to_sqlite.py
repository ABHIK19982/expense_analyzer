"""
Author: Abhik Pramanik
Change Date: 2026-08-07
Change details: One-time migration of user_details rows from MySQL to SQLite.
Migrates all rows from a legacy MySQL ``user_details`` table into the local
SQLite metastore used by the FastAPI application.
Inputs: ``MYSQL_HOST``, ``MYSQL_USER``, ``MYSQL_PASSWORD``, ``MYSQL_DB`` env vars
        and optional ``SQLITE_DB_PATH`` (default ``data/metastore.db``).
Outputs: Populated SQLite file; prints migrated/skipped row counts to stdout.
Usage:
    cd backend
    uv run --with pymysql python scripts/migrate_mysql_to_sqlite.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.config import get_settings  # noqa: E402
from app.database import Base, init_db  # noqa: E402
from app.models.user import User  # noqa: E402


def _mysql_uri() -> str:
    """
    Purpose: Build a MySQL SQLAlchemy URI from environment variables.
    Inputs: ``MYSQL_HOST``, ``MYSQL_USER``, ``MYSQL_PASSWORD``, ``MYSQL_DB``.
    Outputs: MySQL connection URI string.
    """
    host = os.environ.get("MYSQL_HOST", "")
    user = os.environ.get("MYSQL_USER", "")
    password = os.environ.get("MYSQL_PASSWORD", "")
    database = os.environ.get("MYSQL_DB", "")
    if not all([host, user, database]):
        raise ValueError(
            "Set MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, and MYSQL_DB for migration."
        )
    return f"mysql+pymysql://{user}:{password}@{host}/{database}"


def migrate_users() -> tuple[int, int]:
    """
    Purpose: Copy all user rows from MySQL into the local SQLite metastore.
    Inputs: MySQL connection via env vars; SQLite path from app settings.
    Outputs: Tuple of (migrated_count, skipped_count).
    """
    settings = get_settings()
    settings.sqlite_db_file.parent.mkdir(parents=True, exist_ok=True)

    mysql_engine = create_engine(
        _mysql_uri(),
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10},
    )
    MySQLSession = sessionmaker(bind=mysql_engine)

    init_db()

    from app.database import SessionLocal as SQLiteSession

    migrated = 0
    skipped = 0

    with MySQLSession() as mysql_db, SQLiteSession() as sqlite_db:
        users = mysql_db.query(User).all()
        for user in users:
            existing = (
                sqlite_db.query(User)
                .filter(User.u_key == user.u_key)
                .first()
            )
            if existing is not None:
                skipped += 1
                continue

            sqlite_db.add(
                User(
                    u_key=user.u_key,
                    uid=user.uid,
                    username=user.username,
                    password=user.password,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    email=user.email,
                    family_size=user.family_size,
                    create_date=user.create_date,
                    end_date=user.end_date,
                    active=user.active,
                )
            )
            migrated += 1

        sqlite_db.commit()

    return migrated, skipped


def main() -> None:
    """
    Purpose: CLI entry point for the MySQL-to-SQLite migration script.
    Inputs: Environment variables for MySQL and optional SQLite path.
    Outputs: None; prints migration summary to stdout.
    """
    migrated, skipped = migrate_users()
    print(f"Migration complete: {migrated} migrated, {skipped} skipped.")


if __name__ == "__main__":
    main()
