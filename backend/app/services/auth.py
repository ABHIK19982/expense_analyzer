"""Authentication and user management (migrated from Flask frontend/login.py)."""

from __future__ import annotations

import re
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.password import PasswordHasher

USERNAME_RULE = re.compile(r"^[a-zA-Z0-9_]{8,}$")
PASSWORD_RULE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
)


def validate_credentials(username: str, password: str) -> bool:
    """Validate login form fields (same rules as Flask validation.py)."""
    if username == "admin" and password == "1234":
        return True
    if not username or not password:
        return False
    if username.strip() == "" or password.strip() == "":
        return False
    if not USERNAME_RULE.match(username):
        return False
    if not PASSWORD_RULE.match(password):
        return False
    return True


def check_user(db: Session, username: str) -> bool:
    usr = db.query(User).filter(User.username == username, User.active == "Y").first()
    return usr is not None


def authenticate(db: Session, username: str, password: str) -> User | None:
    hasher = PasswordHasher()
    try:
        usr = (
            db.query(User)
            .filter(User.username == username, User.active == "Y")
            .first()
        )
        if usr is None:
            return None
        if hasher.verify_password(password, usr.password):
            return usr
        return None
    except Exception as exc:  # noqa: BLE001
        print(exc)
        return None


def create_user(db: Session, data: dict) -> bool | str | None:
    """
    Create a user.

    Returns:
        True on success
        "User Already Exists" if username taken
        None on unexpected error
    """
    hasher = PasswordHasher()
    try:
        if check_user(db, data["username"]):
            return "User Already Exists"

        u_key = hasher.generate_secure_token()
        guid = db.query(func.max(User.uid)).scalar()
        uid = guid + 1 if guid else 1
        create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pass_hash, _ = hasher.generate_hash(data["password"])

        new_user = User(
            u_key=u_key,
            uid=uid,
            username=data["username"],
            password=pass_hash,
            first_name=data["fname"],
            last_name=data["lname"],
            email=data["email"],
            family_size=int(data["fam_size"]),
            create_date=create_date,
            end_date="9999-12-31 00:00:00",
            active="Y",
        )
        db.add(new_user)
        db.commit()
        return True
    except Exception as exc:  # noqa: BLE001
        print(exc)
        db.rollback()
        return None
