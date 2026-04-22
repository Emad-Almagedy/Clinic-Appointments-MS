from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models import UserRole

class UserBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(min_length=1, max_length=50)
    phone_number: str = Field(min_length=9)
    role: UserRole
    speciality: Optional[str] = None
    is_active: bool = True 
    
class UserCreate(UserBase):
    password: str = Field(min_length=8)
    
    class Config:
        extra = "forbid"
        
class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = Field(None, min_length=1, max_length=50)
    phone_number: Optional[str] = Field(None, min_length=9)
    role: Optional[UserRole] = None
    speciality: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)

class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    display_id: int  
    created_at: datetime
    
    # class Config:
    #     from_attributes = True  
    
class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    full_name: str
    role: UserRole
    created_at: datetime
    
class UserPrivate(UserPublic):
    email: EmailStr 
    phone_number: str
    is_active:bool 
    speciality: Optional[str]
    

        