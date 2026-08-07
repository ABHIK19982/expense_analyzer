"""
Author: Abhik Pramanik
Change Date: 2026-08-07
Change details: Background worker to sync SQLite user_details rows to MySQL backup.
MySQL backup service for the Expense Analyzer metastore.
Reads all user rows from the primary SQLite database and overwrites the MySQL
``user_details`` table on a configurable interval.
Inputs: settings from ``get_settings()``; SQLite session from ``SessionLocal``.
Outputs: ``sync_sqlite_to_mysql()`` row count; ``MySQLBackupWorker`` asyncio loop.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.database import Base, SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)


def sync_sqlite_to_mysql() -> int:
    """
    Purpose: Copy all user rows from SQLite to MySQL, fully overwriting MySQL data.
    Inputs: Primary SQLite ``SessionLocal``; MySQL URI from ``get_settings()``.
    Outputs: Number of rows written to MySQL; raises on unrecoverable MySQL errors.
    """
    settings = get_settings()
    mysql_engine = create_engine(
        settings.mysql_backup_database_uri,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )
    MySQLSession = sessionmaker(autocommit=False, autoflush=False, bind=mysql_engine)

    Base.metadata.create_all(bind=mysql_engine)

    with SessionLocal() as sqlite_db, MySQLSession() as mysql_db:
        users = sqlite_db.query(User).all()
        mysql_db.query(User).delete()
        for user in users:
            mysql_db.add(
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
        mysql_db.commit()
        return len(users)


class MySQLBackupWorker:
    """Async background worker that periodically syncs SQLite users to MySQL."""

    def __init__(self) -> None:
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """
        Purpose: Start the background MySQL backup loop when enabled in settings.
        Inputs: ``mysql_backup_enabled`` and ``mysql_backup_interval_seconds`` settings.
        Outputs: None; schedules an asyncio task if backup is enabled.
        """
        settings = get_settings()
        if not settings.mysql_backup_enabled:
            logger.info("MySQL backup worker is disabled")
            return
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "MySQL backup worker started (interval=%ss)",
            settings.mysql_backup_interval_seconds,
        )

    async def stop(self) -> None:
        """
        Purpose: Cancel the background backup task on application shutdown.
        Inputs: None.
        Outputs: None; cancels and awaits the backup asyncio task if running.
        """
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
        logger.info("MySQL backup worker stopped")

    async def _run_loop(self) -> None:
        """
        Purpose: Run full-table sync immediately, then repeat on the configured interval.
        Inputs: ``mysql_backup_interval_seconds`` from settings.
        Outputs: None; logs sync results and retries after each interval.
        """
        settings = get_settings()
        while True:
            try:
                row_count = await asyncio.to_thread(sync_sqlite_to_mysql)
                logger.info("MySQL backup sync complete: %s rows", row_count)
            except Exception:  # noqa: BLE001
                logger.exception("MySQL backup sync failed")
            await asyncio.sleep(settings.mysql_backup_interval_seconds)
