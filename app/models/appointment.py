import uuid
from uuid import UUID
from typing import List, Optional
from datetime import date, time, datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Integer
from enum import Enum

class AppointmentStatus(str, Enum):
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class Appointment(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    display_id: Optional[int] = Field(sa_column=Column(Integer, autoincrement=True, unique=True, index=True, nullable=True),default=None)    

    appointment_date: date
    appointment_time: time
    status: AppointmentStatus = Field(default=AppointmentStatus.SCHEDULED)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Foreign Keys 
    patient_id: UUID = Field(foreign_key="patient.id")
    doctor_id: UUID = Field(foreign_key="user.id")

    # Relationships
    patient: "Patient" = Relationship(back_populates="appointments")
    doctor: "User" = Relationship(back_populates="doctor_appointments")
    note: Optional["VisitNote"] = Relationship(back_populates="appointment", sa_relationship_kwargs={"uselist": False})

class VisitNote(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    content: str 
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    appointment_id: UUID = Field(foreign_key="appointment.id", unique=True)
    doctor_id: UUID = Field(foreign_key="user.id")

    appointment: Appointment = Relationship(back_populates="note")
    doctor: "User" = Relationship(back_populates="authored_notes")