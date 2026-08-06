"""SQLAlchemy User model (MySQL metastore)."""

from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "user_details"

    u_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    uid: Mapped[int] = mapped_column(Integer, nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    family_size: Mapped[int] = mapped_column(Integer, nullable=False)
    create_date: Mapped[str] = mapped_column(String(30), nullable=False)
    end_date: Mapped[str] = mapped_column(String(30), nullable=False)
    active: Mapped[str] = mapped_column(String(1), nullable=False)
