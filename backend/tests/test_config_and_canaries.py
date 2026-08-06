import pytest

from app.canaries.generator import TOKEN_PREFIX, generate_tokens
from app.config import Settings
from app.models.canary import CanaryType


def test_url_tokens_are_unique_and_do_not_embed_a_domain():
    tokens = generate_tokens(CanaryType.URL, 3)
    assert len(set(tokens)) == 3
    assert all(token.startswith(f"{TOKEN_PREFIX}-") for token in tokens)
    assert all("//" not in token for token in tokens)


def test_safe_development_configuration_is_accepted():
    Settings(
        deployment_mode="development",
        secret_key="s" * 32,
        admin_password="local-password",
    ).validate_runtime()


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"secret_key": "too-short"}, "SECRET_KEY"),
        ({"admin_password_hash": "", "admin_password": ""}, "ADMIN_PASSWORD_HASH"),
        ({"session_expire_minutes": 2}, "SESSION_EXPIRE_MINUTES"),
    ],
)
def test_development_configuration_rejects_unsafe_runtime(overrides, expected):
    values = {
        "deployment_mode": "development",
        "secret_key": "s" * 32,
        "admin_password": "local-password",
    }
    values.update(overrides)
    with pytest.raises(RuntimeError, match=expected):
        Settings(**values).validate_runtime()


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"secret_key": "too-short"}, "SECRET_KEY"),
        ({"app_base_url": "http://example.test"}, "APP_BASE_URL"),
        ({"canary_base_url": "http://example.test"}, "CANARY_BASE_URL"),
        ({"cors_origins": ["*"]}, "CORS_ORIGINS"),
        ({"admin_password": "plaintext"}, "ADMIN_PASSWORD must not be used"),
    ],
)
def test_production_configuration_rejects_unsafe_values(overrides, expected):
    values = {
        "deployment_mode": "production",
        "secret_key": "s" * 32,
        "admin_password": "",
        "admin_password_hash": "$2b$12$not-a-real-hash-for-validation-only",
        "app_base_url": "https://example.test",
        "canary_base_url": "https://example.test",
        "cors_origins": ["https://example.test"],
    }
    values.update(overrides)
    with pytest.raises(RuntimeError, match=expected):
        Settings(**values).validate_runtime()
