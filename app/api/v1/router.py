from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, appointments

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# api_router.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
