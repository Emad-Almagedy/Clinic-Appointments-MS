from pydantic import BaseModel, EmailStr
from uuid import UUID
from app.models import UserRole

class Token(BaseModel):
    access_token: str
    token_type: str 
