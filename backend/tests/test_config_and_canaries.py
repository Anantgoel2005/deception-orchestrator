from app.canaries.generator import TOKEN_PREFIX, generate_tokens
from app.config import Settings
from app.models.canary import CanaryType


def test_url_tokens_are_unique_and_do_not_embed_a_domain():
    tokens = generate_tokens(CanaryType.URL, 3)
    assert len(set(tokens)) == 3
    assert all(token.startswith(f"{TOKEN_PREFIX}-") for token in tokens)
    assert all("//" not in token for token in tokens)


def test_production_configuration_requires_safe_values():
    settings = Settings(
        deployment_mode="production", secret_key="too-short", app_base_url="http://example.test",
        canary_base_url="http://example.test", admin_password_hash="",
    )
    try:
        settings.validate_runtime()
    except RuntimeError as exc:
        assert "Unsafe production configuration" in str(exc)
    else:
        raise AssertionError("unsafe production configuration was accepted")
