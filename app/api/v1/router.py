from fastapi import APIRouter
from app.api.v1.endpoints import auth, doctor, admin, reception

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(doctor.router, prefix="/doctor", tags=["Doctor"])
api_router.include_router(reception.router, prefix="/reception", tags=["Reception"])

