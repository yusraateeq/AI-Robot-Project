import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from src.config.settings import settings


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    return salt + ":" + hashlib.sha256((salt + password).encode()).hexdigest()


def verify_password(password: str, pw_hash: str) -> bool:
    salt, stored = pw_hash.split(":")
    return stored == hashlib.sha256((salt + password).encode()).hexdigest()


def create_jwt(user_id: int, username: str, firebase_uid: str | None = None) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "iat": datetime.now(timezone.utc),
    }
    if firebase_uid:
        payload["firebase_uid"] = firebase_uid
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except Exception:
        return None
