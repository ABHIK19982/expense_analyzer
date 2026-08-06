"""bcrypt password hashing utility (migrated from scripts/passwordhash.py)."""

from __future__ import annotations

import base64
import secrets

import bcrypt


class PasswordHasher:
    def __init__(self, rounds: int = 12) -> None:
        self.rounds = rounds

    def generate_hash(self, password: str) -> tuple[str, str]:
        if not isinstance(password, str):
            raise ValueError("Password must be a string")
        if not password:
            raise ValueError("Password cannot be empty")

        salt = bcrypt.gensalt(rounds=self.rounds)
        password_bytes = password.encode("utf-8")
        password_hash = bcrypt.hashpw(password_bytes, salt)
        return password_hash.decode("utf-8"), salt.decode("utf-8")

    def verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                stored_hash.encode("utf-8"),
            )
        except Exception as exc:  # noqa: BLE001
            print(f"Error verifying password: {exc}")
            return False

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        return base64.urlsafe_b64encode(secrets.token_bytes(length)).decode("utf-8")
