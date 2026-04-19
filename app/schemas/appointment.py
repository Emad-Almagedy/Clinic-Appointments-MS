from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, time, datetime
from app.models import AppointmentStatus
from app.schemas.patient import PatientRead

# --- visit note schema ---

class VisitNoteBase(BaseModel):
    content: str

class VisitNoteCreate(VisitNoteBase):
    pass
    
class VisitNoteRead(VisitNoteBase):
    id: UUID
    doctor_id: UUID
    timestamp: datetime
    
    class Config:
        from_attributes = True


    
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
    created_at: datetime
    patient: PatientRead
    doctor_id: UUID
    # allows to see the note attached to the appointment
    note: Optional[VisitNoteRead] = None
    
    class Config:
        from_attributes = True
            

# --- Doctor Dashboard Schemas ---

class DoctorDashboardStats(BaseModel):
    todays_appointments: int
    upcoming_appointments: int
    total_patients: int
    visit_notes_total: int