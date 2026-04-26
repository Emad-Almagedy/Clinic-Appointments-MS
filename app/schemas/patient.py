from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import date, datetime

class PatientBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=50)
    national_id: str = Field(min_length=1, max_length=50)
    email: EmailStr 
    phone_number: str = Field(min_length=9)
    date_of_birth: date

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=50)
    national_id: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, min_length=9)
    date_of_birth: Optional[date] = None

class PatientRead(PatientBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    display_id: int
    created_at: datetime
    
    # class Config:
    #     from_attributes = True
    
    