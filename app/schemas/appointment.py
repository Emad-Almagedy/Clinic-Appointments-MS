from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, time, datetime
from app.models import AppointmentStatus

# --- visit note schema ---

class VisitNoteBase(BaseModel):
    content: str

class VisitNoteCreate(VisitNoteBase):
    appointment_id: UUID

class VisitNoteRead(VisitNoteBase):
    id: UUID
    timestamp: datetime
    doctor_id: UUID


    
# --- Appointment schemas ---

class AppointmentBase(BaseModel):
    appointment_date: date
    appointment_time: time
    status: AppointmentStatus = AppointmentStatus.SCHEDULED 

class AppointmentCreate(AppointmentBase):
    patient_id: UUID
    doctor_id: UUID       

class AppointmentRead(AppointmentBase):
    id: UUID
    display_id: int
    patient_id: UUID
    doctor_id: UUID
    # allows to see the note attached to the appointment
    note: Optional[VisitNoteRead] = None
    
    class Config:
        from_attributes = True
            
