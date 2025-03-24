from fastapi import APIRouter

from app.routes.health_router import router as health_router
from app.routes.users_router import router as users_router

router = APIRouter()
router.include_router(health_router)
router.include_router(users_router)