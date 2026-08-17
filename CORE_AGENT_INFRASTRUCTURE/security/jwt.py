"""
JWT (HS256) — stdlib-only implementation, secret from config only.

Claims: sub (user id), email, role, iat, exp. Token TTL from config.
"""
import base64
import hashlib
import hmac
import json
import time

from CORE_AGENT_INFRASTRUCTURE.config import get_config


class JWTError(RuntimeError):
    pass


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64url(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_token(user_id: int, email: str, role: str, ttl_hours: int | None = None) -> str:
    cfg = get_config()
    ttl = ttl_hours or cfg.token_ttl_hours
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "iat": now,
        "exp": now + ttl * 3600,
    }
    signing_input = _b64url(json.dumps(header, separators=(",", ":")).encode()) + "." +         _b64url(json.dumps(payload, separators=(",", ":")).encode())
    signature = hmac.new(cfg.jwt_secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    return signing_input + "." + _b64url(signature)


def decode_token(token: str) -> dict:
    cfg = get_config()
    try:
        signing_input, signature_b64 = token.rsplit(".", 1)
        header_b64, payload_b64 = signing_input.split(".")
        expected = hmac.new(cfg.jwt_secret.encode(), signing_input.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _unb64url(signature_b64)):
            raise JWTError("invalid signature")
        payload = json.loads(_unb64url(payload_b64))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise JWTError("token expired")
        return payload
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        raise JWTError("malformed token") from exc
