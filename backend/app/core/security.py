"""Small signed bearer tokens for the assignment demo; swap for NOVA SSO in production."""

import base64
import hashlib
import hmac
import json
import secrets
import time

from fastapi import HTTPException

from app.core.config import settings


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"{base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        salt_text, digest_text = encoded.split("$", 1)
        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = base64.urlsafe_b64decode(digest_text.encode())
    except (ValueError, TypeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return hmac.compare_digest(actual, expected)


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def create_access_token(user_id: str, organization_id: str) -> tuple[str, int]:
    expires_in = settings.access_token_expire_minutes * 60
    payload = {"sub": user_id, "org": organization_id, "exp": int(time.time()) + expires_in}
    encoded_payload = _encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = _encode(hmac.new(settings.auth_secret.encode(), encoded_payload.encode(), hashlib.sha256).digest())
    return f"{encoded_payload}.{signature}", expires_in


def decode_access_token(token: str) -> dict:
    try:
        encoded_payload, signature = token.split(".", 1)
        expected = _encode(hmac.new(settings.auth_secret.encode(), encoded_payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("signature")
        payload = json.loads(base64.urlsafe_b64decode(encoded_payload + "=" * (-len(encoded_payload) % 4)))
        if int(payload["exp"]) <= int(time.time()) or not payload.get("sub") or not payload.get("org"):
            raise ValueError("expired or incomplete")
        return payload
    except (ValueError, KeyError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise HTTPException(status_code=401, detail={"code": "invalid_or_expired_token"}) from error
