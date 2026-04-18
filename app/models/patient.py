import uuid
from uuid import UUID
from typing import List, Optional
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Integer

class Patient(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    display_id: Optional[int] = Field(sa_column=Column(Integer, autoincrement=True, unique=True, index=True, nullable=True),default=None)    
    full_name: str = Field(index=True)
    national_id: str = Field(unique=True, index=True)
    email: str
    phone_number: str
    date_of_birth: date
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    appointments: List["Appointment"] = Relationship(back_populates="patient")   