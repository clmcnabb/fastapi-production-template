import asyncio
import json
from datetime import UTC, datetime

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import require_user
from app.core.security import decode_access_token
from app.db.session import get_db
from app.services.realtime_service import realtime_hub
from app.services.user_service import get_user

router = APIRouter()


class StreamMessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


def _format_sse(event_name: str, data: dict[str, object]) -> str:
    return f"event: {event_name}\\ndata: {json.dumps(data)}\\n\\n"


def _get_websocket_token(websocket: WebSocket) -> str | None:
    auth_header = websocket.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", maxsplit=1)[1]
    return websocket.query_params.get("token")


def _get_websocket_user(websocket: WebSocket, db: Session) -> object:
    token = _get_websocket_token(websocket)
    if token is None:
        raise WebSocketException(code=1008, reason="Missing authentication token")

    subject = decode_access_token(token)
    if subject is None or not subject.isdigit():
        raise WebSocketException(code=1008, reason="Invalid authentication token")

    user = get_user(db, int(subject))
    if user is None:
        raise WebSocketException(code=1008, reason="User not found")

    return user


@router.get("/sse")
async def sse_stream(
    request: Request,
    max_events: int | None = Query(default=None, ge=1, le=1000),
    current_user=Depends(require_user),
) -> StreamingResponse:
    subscriber_id, queue = await realtime_hub.register_sse()

    async def event_generator():
        sent_events = 0
        try:
            connected_event = {
                "type": "connected",
                "user_id": current_user.id,
                "timestamp": datetime.now(UTC).isoformat(),
            }
            yield _format_sse("connected", connected_event)
            sent_events += 1

            while True:
                if max_events is not None and sent_events >= max_events:
                    break
                if await request.is_disconnected():
                    break

                try:
                    message = await asyncio.wait_for(queue.get(), timeout=15)
                    payload = json.loads(message)
                    yield _format_sse("message", payload)
                    sent_events += 1
                except TimeoutError:
                    yield ": keep-alive\\n\\n"
        finally:
            await realtime_hub.unregister_sse(subscriber_id)

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)


@router.post("/messages", status_code=202)
async def publish_message(
    payload: StreamMessageCreate,
    current_user=Depends(require_user),
) -> dict[str, int]:
    event = {
        "type": "message",
        "user_id": current_user.id,
        "message": payload.message,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    await realtime_hub.broadcast(event)
    return await realtime_hub.counts()


@router.websocket("/ws")
async def websocket_stream(websocket: WebSocket, db: Session = Depends(get_db)) -> None:
    current_user = _get_websocket_user(websocket, db)
    await websocket.accept()
    await realtime_hub.add_websocket(websocket)

    await websocket.send_json(
        {
            "type": "connected",
            "user_id": current_user.id,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )

    try:
        while True:
            message_text = await websocket.receive_text()
            event = {
                "type": "message",
                "user_id": current_user.id,
                "message": message_text,
                "timestamp": datetime.now(UTC).isoformat(),
            }
            await realtime_hub.broadcast(event)
    except WebSocketDisconnect:
        pass
    finally:
        await realtime_hub.remove_websocket(websocket)
