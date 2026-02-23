import asyncio
import json
import logging
from collections.abc import Iterable
from contextlib import suppress

from fastapi import WebSocket
from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RealtimeHub:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._next_subscriber_id = 0
        self._sse_subscribers: dict[int, asyncio.Queue[str]] = {}
        self._websocket_connections: set[WebSocket] = set()

        self._redis_url: str | None = None
        self._redis_channel = "realtime:events"
        self._redis_client: Redis | None = None
        self._redis_pubsub_task: asyncio.Task[None] | None = None

    def configure(self, redis_url: str | None, redis_channel: str) -> None:
        self._redis_url = redis_url or None
        self._redis_channel = redis_channel

    async def start(self) -> None:
        if self._redis_url is None:
            return

        try:
            self._redis_client = Redis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._redis_client.ping()
            self._redis_pubsub_task = asyncio.create_task(self._consume_redis_pubsub())
            logger.info("Realtime Redis backend enabled channel=%s", self._redis_channel)
        except RedisError:
            logger.exception(
                "Unable to connect to Redis backend; "
                "falling back to in-process realtime broadcasting"
            )
            if self._redis_client is not None:
                await self._redis_client.aclose()
            self._redis_client = None

    async def stop(self) -> None:
        if self._redis_pubsub_task is not None:
            self._redis_pubsub_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._redis_pubsub_task
            self._redis_pubsub_task = None

        if self._redis_client is not None:
            await self._redis_client.aclose()
            self._redis_client = None

    async def register_sse(self) -> tuple[int, asyncio.Queue[str]]:
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
        async with self._lock:
            subscriber_id = self._next_subscriber_id
            self._next_subscriber_id += 1
            self._sse_subscribers[subscriber_id] = queue
        return subscriber_id, queue

    async def unregister_sse(self, subscriber_id: int) -> None:
        async with self._lock:
            self._sse_subscribers.pop(subscriber_id, None)

    async def add_websocket(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._websocket_connections.add(websocket)

    async def remove_websocket(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._websocket_connections.discard(websocket)

    async def broadcast(self, payload: dict[str, object]) -> None:
        message = json.dumps(payload)

        if self._redis_client is not None:
            try:
                await self._redis_client.publish(self._redis_channel, message)
                return
            except RedisError:
                logger.exception(
                    "Failed to publish realtime event to Redis; using in-process fallback"
                )

        await self._broadcast_local(message)

    async def _consume_redis_pubsub(self) -> None:
        if self._redis_client is None:
            return

        pubsub = self._redis_client.pubsub()
        try:
            await pubsub.subscribe(self._redis_channel)
            while True:
                event = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if event is None:
                    await asyncio.sleep(0.01)
                    continue

                message = event.get("data")
                if not isinstance(message, str):
                    continue

                await self._broadcast_local(message)
        finally:
            await pubsub.unsubscribe(self._redis_channel)
            await pubsub.aclose()

    async def _broadcast_local(self, message: str) -> None:
        async with self._lock:
            sse_queues = list(self._sse_subscribers.values())
            ws_connections = list(self._websocket_connections)

        self._fan_out_sse(message, sse_queues)

        stale_websockets: list[WebSocket] = []
        for websocket in ws_connections:
            try:
                await websocket.send_text(message)
            except RuntimeError:
                stale_websockets.append(websocket)

        if stale_websockets:
            async with self._lock:
                for websocket in stale_websockets:
                    self._websocket_connections.discard(websocket)

    def _fan_out_sse(self, message: str, queues: Iterable[asyncio.Queue[str]]) -> None:
        for queue in queues:
            if queue.full():
                with suppress(asyncio.QueueEmpty):
                    queue.get_nowait()
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                continue

    async def counts(self) -> dict[str, int]:
        async with self._lock:
            return {
                "sse_connections": len(self._sse_subscribers),
                "ws_connections": len(self._websocket_connections),
            }


realtime_hub = RealtimeHub()
