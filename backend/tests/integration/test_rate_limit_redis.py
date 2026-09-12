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
