import uuid
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.config import settings
from app.core.exceptions import NotAuthenticatedException
from app.services.token_service import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_refresh_token,
    refresh_token_expires_at,
)


def test_create_access_token_returns_string():
    token = create_access_token(uuid.uuid4())
    assert isinstance(token, str) and len(token) > 0


def test_decode_access_token_returns_correct_user_id():
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    assert decode_access_token(token) == user_id


def test_decode_access_token_invalid_token_raises():
    with pytest.raises(NotAuthenticatedException):
        decode_access_token("not.a.valid.token")


def test_decode_access_token_tampered_token_raises():
    token = create_access_token(uuid.uuid4())
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(NotAuthenticatedException):
        decode_access_token(tampered)


def test_decode_access_token_expired_raises():
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(uuid.uuid4()),
        "exp": now - timedelta(seconds=1),
        "iat": now - timedelta(minutes=31),
        "jti": str(uuid.uuid4()),
    }
    expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    with pytest.raises(NotAuthenticatedException):
        decode_access_token(expired_token)


def test_decode_access_token_missing_sub_raises():
    now = datetime.now(timezone.utc)
    payload = {"exp": now + timedelta(minutes=30), "iat": now, "jti": str(uuid.uuid4())}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    with pytest.raises(NotAuthenticatedException):
        decode_access_token(token)


def test_create_refresh_token_returns_raw_and_sha256_hash():
    raw, token_hash = create_refresh_token()
    assert isinstance(raw, str) and len(raw) > 0
    assert isinstance(token_hash, str) and len(token_hash) == 64  # SHA-256 hex
    assert raw != token_hash


def test_create_refresh_token_unique_on_each_call():
    raw1, hash1 = create_refresh_token()
    raw2, hash2 = create_refresh_token()
    assert raw1 != raw2
    assert hash1 != hash2


def test_hash_refresh_token_is_deterministic():
    raw = "some-fixed-token-value"
    assert hash_refresh_token(raw) == hash_refresh_token(raw)


def test_refresh_token_expires_at_is_in_future():
    assert refresh_token_expires_at() > datetime.now(timezone.utc)


def test_refresh_token_expires_at_correct_duration():
    before = datetime.now(timezone.utc)
    expires = refresh_token_expires_at()
    expected = before + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    assert abs((expires - expected).total_seconds()) < 5
