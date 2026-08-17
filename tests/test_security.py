from CORE_AGENT_INFRASTRUCTURE.security.hashing import hash_password, verify_password
from CORE_AGENT_INFRASTRUCTURE.security.jwt import JWTError, create_token, decode_token


def test_password_hash_roundtrip():
    stored = hash_password("correct horse battery staple")
    assert stored.startswith("pbkdf2$")
    assert verify_password("correct horse battery staple", stored)
    assert not verify_password("wrong password", stored)


def test_password_hashes_are_salted():
    assert hash_password("same-password") != hash_password("same-password")


def test_jwt_roundtrip():
    token = create_token(7, "owner@stratum.local", "owner")
    payload = decode_token(token)
    assert payload["sub"] == "7"
    assert payload["role"] == "owner"
    assert payload["email"] == "owner@stratum.local"


def test_jwt_tamper_rejected():
    token = create_token(7, "a@b.c", "viewer")
    tampered = token[:-2] + ("AB" if token[-2:] != "AB" else "CD")
    try:
        decode_token(tampered)
        raised = False
    except JWTError:
        raised = True
    assert raised
