"""Unit tests for JWT and password helpers."""

import pytest
from fastapi import HTTPException
import jwt

from app.auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    _decode_token,
)
from app.config import get_settings


def test_password_hash_roundtrip():
    hashed = hash_password("s3cret-pw")
    assert hashed != "s3cret-pw"
    assert verify_password("s3cret-pw", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_access_and_refresh_tokens_decode():
    access = create_access_token("alice")
    refresh = create_refresh_token("alice")

    assert _decode_token(access, "access") == "alice"
    assert _decode_token(refresh, "refresh") == "alice"


def test_decode_rejects_wrong_token_type():
    refresh = create_refresh_token("alice")

    with pytest.raises(HTTPException) as exc:
        _decode_token(refresh, "access")

    assert exc.value.status_code == 401


def test_decode_rejects_tampered_token():
    settings = get_settings()
    bad = jwt.encode(
        {"sub": "alice", "type": "access"},
        "wrong-secret",
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(HTTPException):
        _decode_token(bad, "access")
