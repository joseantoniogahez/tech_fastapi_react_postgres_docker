from pathlib import Path

import yaml  # type: ignore[import-untyped]

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_rate_limit_runbook_covers_runtime_security_and_failure_contracts() -> None:
    runbook = (REPOSITORY_ROOT / "backend/docs/operations/rate_limiting.md").read_text(encoding="utf-8")
    required_terms = (
        "fixed-window",
        "POST /v1/token",
        "POST /v1/users/register",
        "10 requests",
        "5 requests",
        "60 seconds",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "Retry-After",
        "request.client.host",
        "Forwarded",
        "X-Forwarded-For",
        "SHA-256",
        "redis:8.8.1-alpine",
        "REDIS_PASSWORD_FILE",
        "REDIS_TIMEOUT_SECONDS",
        "INCR",
        "EXPIRE",
        "TTL",
        "aclose()",
        "429 rate_limited",
        "503 service_unavailable",
    )
    assert [term for term in required_terms if term not in runbook] == []


def test_compose_redis_is_pinned_private_authenticated_and_readiness_bound() -> None:
    compose = yaml.safe_load((REPOSITORY_ROOT / "compose.yaml").read_text(encoding="utf-8"))
    redis_service = compose["services"]["redis"]
    backend_service = compose["services"]["backend"]

    assert redis_service["image"] == "redis:8.8.1-alpine"
    assert "ports" not in redis_service
    assert redis_service["secrets"] == ["redis_password"]
    assert "/run/secrets/redis_password" in " ".join(redis_service["command"])
    assert "/run/secrets/redis_password" in " ".join(redis_service["healthcheck"]["test"])
    assert compose["secrets"]["redis_password"] == {"environment": "REDIS_PASSWORD"}

    assert backend_service["depends_on"]["redis"] == {"condition": "service_healthy"}
    environment = backend_service["environment"]
    assert "REDIS_PASSWORD" not in environment
    assert environment["REDIS_PASSWORD_FILE"] == "/run/secrets/redis_password"
    assert environment["REDIS_ALLOW_PLAINTEXT"] == "true"
    assert environment["REDIS_TIMEOUT_SECONDS"] == "${REDIS_TIMEOUT_SECONDS:-2}"
    assert environment["RATE_LIMIT_STORAGE"] == "redis"
    assert environment["REDIS_URL"] == "redis://redis:6379/0"


def test_production_and_non_compose_configuration_require_explicit_security_values() -> None:
    production = (REPOSITORY_ROOT / "compose.prod.yaml").read_text(encoding="utf-8")
    for name in (
        "RATE_LIMIT_LOGIN",
        "RATE_LIMIT_REGISTER",
        "RATE_LIMIT_WINDOW_SECONDS",
    ):
        assert f"${{{name}:?{name} is required in prod}}" in production

    environment_example = (REPOSITORY_ROOT / ".env_examples").read_text(encoding="utf-8")
    for expected in (
        "RATE_LIMIT_ENABLED=true",
        "RATE_LIMIT_STORAGE=memory",
        "RATE_LIMIT_LOGIN=10",
        "RATE_LIMIT_REGISTER=5",
        "RATE_LIMIT_WINDOW_SECONDS=60",
        "REDIS_URL=rediss://",
        "REDIS_PASSWORD=REPLACE_ME",
        "REDIS_ALLOW_PLAINTEXT=false",
        "REDIS_TIMEOUT_SECONDS=2",
    ):
        assert expected in environment_example
