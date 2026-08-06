from datetime import datetime, timedelta, timezone

import pytest
from jose import JWTError, jwt

from app.api.dependencies import csrf_tokens_match, decode_session_token
from app.config import settings
from app.core.rate_limit import FixedWindowRateLimiter


def _token(**overrides):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": settings.admin_username,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "jti": "test-session",
    }
    payload.update(overrides)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def test_session_token_requires_expected_identity_issuer_and_audience():
    assert decode_session_token(_token())["sub"] == settings.admin_username
    with pytest.raises(JWTError):
        decode_session_token(_token(sub="unknown"))
    with pytest.raises(JWTError):
        decode_session_token(_token(aud="other-service"))
    with pytest.raises(JWTError):
        decode_session_token(_token(iss="other-issuer"))


def test_csrf_tokens_require_nonempty_constant_time_match():
    assert csrf_tokens_match("same-token", "same-token")
    assert not csrf_tokens_match("same-token", "different-token")
    assert not csrf_tokens_match(None, "same-token")
    assert not csrf_tokens_match("same-token", None)


def test_rate_limiter_enforces_limit_and_can_reset():
    limiter = FixedWindowRateLimiter()
    assert limiter.allowed("login:127.0.0.1", limit=2, seconds=60)
    assert limiter.allowed("login:127.0.0.1", limit=2, seconds=60)
    assert not limiter.allowed("login:127.0.0.1", limit=2, seconds=60)
    limiter.reset()
    assert limiter.allowed("login:127.0.0.1", limit=2, seconds=60)
