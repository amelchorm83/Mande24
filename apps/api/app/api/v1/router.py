from fastapi import APIRouter

from app.api.v1.endpoints_auth import router as auth_router
from app.api.v1.endpoints_catalogs import router as catalogs_router
from app.api.v1.endpoints_commissions import router as commissions_router
from app.api.v1.endpoints_guides import router as guides_router
from app.api.v1.endpoints_health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(catalogs_router)
api_router.include_router(commissions_router)
api_router.include_router(guides_router)
