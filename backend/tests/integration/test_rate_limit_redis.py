import asyncio
import os
from uuid import uuid4

import pytest

from app.core.rate_limit import RedisCounterStore
from app.features.health.schemas import ReadinessStatus
from app.features.health.service import ReadinessCheckDefinition, ReadinessCheckRegistry, ReadinessService


def test_real_redis_increment_is_atomic_across_clients_and_closes() -> None:
    redis_url = os.getenv("TEST_REDIS_URL")
    redis_password = os.getenv("TEST_REDIS_PASSWORD")
    if not redis_url or not redis_password:
        pytest.skip("Set TEST_REDIS_URL and TEST_REDIS_PASSWORD for the ephemeral Redis integration gate.")

    async def run_test() -> None:
        first = RedisCounterStore(redis_url, redis_password)
        second = RedisCounterStore(redis_url, redis_password)
        key = f"foundation:rate-limit:integration:{uuid4().hex}"
        try:
            await first.ping()
            results = await asyncio.gather(*(store.increment(key, 60) for store in (first, second) for _ in range(5)))
            counts = sorted(count for count, _ttl in results)
            ttls = [ttl for _count, ttl in results]
            assert counts == list(range(1, 11))
            assert all(1 <= ttl <= 60 for ttl in ttls)

            registry = ReadinessCheckRegistry([ReadinessCheckDefinition("redis", first.ping)])
            readiness = await ReadinessService(
                registry,
                timeout_seconds=2,
                max_concurrency=1,
            ).evaluate()
            assert readiness.status == ReadinessStatus.OK
            assert [(check.name, check.status) for check in readiness.checks] == [("redis", ReadinessStatus.OK)]
        finally:
            await first.aclose()
            await second.aclose()

    asyncio.run(run_test())


@pytest.mark.parametrize("remaining_ms", [200, None])
def test_real_redis_preserves_expiry_and_repairs_only_missing_expiry(remaining_ms: int | None) -> None:
    redis_url = os.getenv("TEST_REDIS_URL")
    redis_password = os.getenv("TEST_REDIS_PASSWORD")
    if not redis_url or not redis_password:
        pytest.skip("Set TEST_REDIS_URL and TEST_REDIS_PASSWORD for the ephemeral Redis integration gate.")

    async def run_test() -> None:
        store = RedisCounterStore(redis_url, redis_password)
        client = store._get_client()
        key = f"foundation:rate-limit:integration:{uuid4().hex}"
        # Redis freezes command time within Lua, so setup and the production script
        # observe exactly the same subsecond expiry without timing-dependent sleeps.
        setup = "redis.call('SET', KEYS[1], 10)\n"
        if remaining_ms is not None:
            setup += f"redis.call('PEXPIRE', KEYS[1], {remaining_ms})\n"
        script = (
            setup
            + "local function increment()\n"
            + RedisCounterStore._INCREMENT_SCRIPT
            + "\nend\nlocal result = increment()\n"
            + "return {result[1], result[2], redis.call('PTTL', KEYS[1])}"
        )
        try:
            result = await client.execute_command("EVAL", script, 1, key, 60)
            assert result == ([11, 0, 200] if remaining_ms is not None else [11, 60, 60000])
        finally:
            try:
                await client.execute_command("DEL", key)
            finally:
                await store.aclose()

    asyncio.run(run_test())
