from pydantic import BaseModel, Field, ConfigDict
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
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    doctor_id: UUID
    timestamp: datetime
    
    # class Config:
    #     from_attributes = True


    
# --- Appointment schemas ---

class AppointmentBase(BaseModel):
    appointment_date: date
    appointment_time: time = Field(description="Appointment time in HH:MM:SS format",examples=["05:30:00"])
    patient_id: UUID
    doctor_id: UUID   
    status: AppointmentStatus 

class AppointmentCreate(AppointmentBase):
    pass
        

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
            
class AppointmentUpdate(BaseModel):
    appointment_date: Optional[date] = None
    appointment_time: Optional[time] = Field(None, description="Appointment time in HH:MM:SS format",examples=["05:30:00"])
    doctor_id: Optional[UUID] = None 
    status: Optional[AppointmentStatus] = None
                

# --- Dashboard Schemas ---
class DoctorDashboardStats(BaseModel):
    todays_appointments: int
    upcoming_appointments: int
    total_patients: int
    visit_notes_total: int
    
class AppointmentStatusSummary(BaseModel):
    scheduled: int
    in_progress: int
    completed: int
    cancelled: int

# --- Admin dashboard stats schema ---
class AdminDashboardStats(BaseModel) :
    total_users: int
    total_doctors: int
    total_patients: int
    total_appointments: int   
    status_summary: AppointmentStatusSummary

# --- Reception stats schemas ---
class ReceptionDashboardStats(BaseModel):
    todays_appointments: int
    upcoming_7_days: int
    total_patients: int
    completed_today: int
    status_summary: AppointmentStatusSummary
    
class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus    