"""FastAPI dependencies (session auth)."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please login to access this page",
        )

    user = (
        db.query(User)
        .filter(User.uid == int(user_id), User.active == "Y")
        .first()
    )
    if user is None:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please login again",
        )
    return user


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User | None:
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    return (
        db.query(User)
        .filter(User.uid == int(user_id), User.active == "Y")
        .first()
    )
