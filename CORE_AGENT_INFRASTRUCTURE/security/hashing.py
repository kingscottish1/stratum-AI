"""
Password hashing — PBKDF2-HMAC-SHA256, 600k iterations, per-user salt.

Format stored:  pbkdf2$600000$<salt_b64>$<hash_b64>
Uses the stdlib only (no bcrypt dependency needed) and constant-time
comparison against timing attacks.
"""
import base64
import hashlib
import hmac
import secrets

ITERATIONS = 600_000
ALGO = "pbkdf2"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"{ALGO}${ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt_b64, hash_b64 = stored.split("$")
        if algo != ALGO:
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(digest, expected)
    except (ValueError, TypeError):
        return False
