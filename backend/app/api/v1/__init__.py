from fastapi import APIRouter
from .endpoints import turbines, valves, calculations, results

api_router = APIRouter()
api_router.include_router(turbines.router)
api_router.include_router(valves.router)
api_router.include_router(calculations.router)
api_router.include_router(results.router) 