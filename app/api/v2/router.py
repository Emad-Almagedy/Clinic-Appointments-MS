from fastapi import APIRouter
from app.api.v2.endpoints import auth, patients, users, settings

api_router_v2 = APIRouter()

api_router_v2.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router_v2.include_router(users.router, prefix="/users", tags=["Users"])
api_router_v2.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router_v2.include_router(patients.router, prefix="/patients", tags=["Patients"])