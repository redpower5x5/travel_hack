from fastapi import APIRouter

# from app.endpoints.auth import router as auth_router
# from app.endpoints.info import router as info_router
# from app.endpoints.admin import router as admin_router
# from app.endpoints.metrics import router as metrics_router
from app.endpoints.uploader import router as uploader_router


router = APIRouter(
    prefix="/api",
    responses={404: {"description": "Not found"}},
)

# router.include_router(auth_router)
# router.include_router(info_router)
# router.include_router(admin_router)
# router.include_router(metrics_router)
router.include_router(uploader_router)
