from typing import List, Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Integer
from enum import Enum
import uuid
from uuid import UUID

class UserRole(str, Enum):
    ADMIN = "Admin"
    DOCTOR = "Doctor"
    RECEPTIONIST = "Receptionist"
    
class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False)
    display_id: Optional[int] = Field(sa_column=Column(Integer, autoincrement=True, unique=True, index=True, nullable=True),default=None)    
    full_name: str = Field(index=True) 
    email: str = Field(unique=True, index=True) 
    phone_number: str
    hashed_password: str
    role: UserRole = Field(index=True)
    speciality: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True) 
    created_at: datetime = Field(default_factory=datetime.utcnow) 

    # Relationships
    doctor_appointments: List["Appointment"] = Relationship(back_populates="doctor")
    authored_notes: List["VisitNote"] = Relationship(back_populates="doctor")  
      