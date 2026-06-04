from fastapi import APIRouter

from app.routers import blood_glucose, blood_pressure, ketones

router = APIRouter(prefix="/api/v1")

router.include_router(blood_pressure.router)
router.include_router(blood_glucose.router)
router.include_router(ketones.router)
