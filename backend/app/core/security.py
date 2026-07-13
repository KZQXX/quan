"""Password hashing and JWT helpers."""

from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import cast

import bcrypt
from jose import JWTError
from jose import jwt

from app.core.config import settings
from app.core.errors import UnauthorizedError


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(user_id: str) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    return cast(
        str,
        jwt.encode(
            {"sub": user_id, "exp": expires_at}, settings.jwt_secret, settings.jwt_algorithm
        ),
    )


def decode_access_token(token: str) -> str:
    try:
        user_id = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]).get(
            "sub"
        )
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired access token") from exc
    if not isinstance(user_id, str):
        raise UnauthorizedError("Invalid access token")
    return user_id
