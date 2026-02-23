import asyncio
import json
import os
import uuid

import pytest
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.services.realtime_service import RealtimeHub


async def _redis_available(redis_url: str) -> bool:
    client = Redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    try:
        await client.ping()
        return True
    except RedisError:
        return False
    finally:
        await client.aclose()


def test_redis_pubsub_fanout_across_hubs() -> None:
    redis_url = os.getenv("REALTIME_TEST_REDIS_URL", "redis://localhost:6379/15")
    if not asyncio.run(_redis_available(redis_url)):
        pytest.skip(f"Redis not available at {redis_url}")

    channel = f"test:realtime:{uuid.uuid4().hex}"

    async def scenario() -> None:
        publisher = RealtimeHub()
        subscriber = RealtimeHub()

        publisher.configure(redis_url, channel)
        subscriber.configure(redis_url, channel)

        await publisher.start()
        await subscriber.start()

        subscriber_id: int | None = None
        try:
            subscriber_id, queue = await subscriber.register_sse()

            payload = {
                "type": "message",
                "message": "cross-instance",
                "source": "publisher",
            }
            await publisher.broadcast(payload)

            raw_message = await asyncio.wait_for(queue.get(), timeout=2)
            assert json.loads(raw_message) == payload
        finally:
            if subscriber_id is not None:
                await subscriber.unregister_sse(subscriber_id)
            await subscriber.stop()
            await publisher.stop()

    asyncio.run(scenario())
