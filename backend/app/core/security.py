import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(*, subject: str, papel: str, transportadora_id: int | None) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": subject,
        "papel": papel,
        "transportadora_id": transportadora_id,
        "type": "access",
        "iat": now,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(*, subject: str) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": subject, "type": "refresh", "iat": now, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Token inválido ou expirado") from exc
    if payload.get("type") != "access":
        raise ValueError("Token inválido ou expirado")
    return payload


def decode_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Token inválido ou expirado") from exc
    if payload.get("type") != "refresh":
        raise ValueError("Token inválido ou expirado")
    return payload


def generate_reset_token() -> tuple[str, str]:
    """Retorna (token_para_enviar_por_email, hash_para_guardar_no_banco)."""
    raw_token = secrets.token_urlsafe(32)
    return raw_token, hash_password(raw_token)


def verify_reset_token(raw_token: str, token_hash: str) -> bool:
    return verify_password(raw_token, token_hash)
