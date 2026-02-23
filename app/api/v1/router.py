from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, predict, stream, users

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(predict.router, prefix="/predict", tags=["predict"])
api_router.include_router(stream.router, prefix="/stream", tags=["stream"])
