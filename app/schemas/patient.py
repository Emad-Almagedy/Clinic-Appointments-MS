from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import date, datetime

class PatientBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=50)
    national_id: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(min_length=1, max_length=50)
    phone_number: str = Field(min_length=9)
    date_of_birth: date

class PatientCreate(PatientBase):
    pass

class PatientRead(PatientBase):
    id: UUID
    display_id: int
    full_name: str
    email:str
    phone_number: str
    date_of_birth: date
    created_at: datetime
    
    class Config:
        from_attributes = True
        
    
    