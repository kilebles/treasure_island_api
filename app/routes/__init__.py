from fastapi import APIRouter

from app.routes.health_router import router as health_router
from app.routes.users_router import router as users_router
from app.routes.lotteries_router import router as lotteries_router
from app.routes.admin_router import router as admin_router
from app.routes.auth_router import router as auth_router

router = APIRouter()
router.include_router(health_router)
router.include_router(users_router)
router.include_router(lotteries_router)
router.include_router(admin_router)
router.include_router(auth_router)
