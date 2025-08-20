from fastapi import APIRouter

from backend.app.api.routes import utils

api_router = APIRouter()

api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
