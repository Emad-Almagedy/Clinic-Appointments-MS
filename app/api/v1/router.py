from fastapi import APIRouter
from app.api.v1.endpoints import doctor, admin, reception, auth 

api_router_v1 = APIRouter()

api_router_v1.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router_v1.include_router(doctor.router, prefix="/doctor", tags=["Doctor"])
api_router_v1.include_router(reception.router, prefix="/reception", tags=["Reception"])
api_router_v1.include_router(auth.router, prefix="/auth", tags=["Authentication"])



