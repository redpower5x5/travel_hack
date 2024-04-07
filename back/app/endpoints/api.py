from fastapi import APIRouter

from app.endpoints.auth import router as auth_router
from app.endpoints.search import router as search_router
# from app.endpoints.admin import router as admin_router
from app.endpoints.account import router as account_router
from app.endpoints.uploader import router as uploader_router


router = APIRouter(
    prefix="/api",
    responses={404: {"description": "Not found"}},
)

router.include_router(auth_router)
router.include_router(search_router)
router.include_router(account_router)
# router.include_router(metrics_router)
router.include_router(uploader_router)
