from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_, or_, String, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models import User, Appointment, Patient, AppointmentStatus
from app.api.v1.dependencies import get_db
from app.core.auth import get_current_user
from app.schemas.patient import PatientCreate, PatientRead
from app.schemas.appointment import AppointmentStatusSummary, ReceptionDashboardStats, ReceptionDashboardStats, AppointmentRead
from app.core.auth import receptionist_only
from typing import Annotated, List, Optional


router = APIRouter()

# --- fetch stats (today's appointments, upcoming (7 days), total patients, completed today)
@router.get("/stats", response_model=ReceptionDashboardStats)
async def get_reception_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(receptionist_only)]
):
    today = date.today()
    next_week = today + timedelta(days=7)

    result = await db.execute(select(func.count(Appointment.id)).where(Appointment.appointment_date == today))
    today_count = result.scalar() or 0

    result = await db.execute(
        select(func.count(Appointment.id))
        .where(and_(Appointment.appointment_date > today, Appointment.appointment_date <= next_week)))
    upcoming_count = result.scalar() or 0

    result = await db.execute(select(func.count(Patient.id)))
    patient_count = result.scalar() or 0

    result = await db.execute(
        select(func.count(Appointment.id))
        .where(and_(Appointment.appointment_date == today, Appointment.status == AppointmentStatus.COMPLETED)
        )
    )
    completed_today = result.scalar() or 0

    return {
        "todays_appointments": today_count,
        "upcoming_7_days": upcoming_count,
        "total_patients": patient_count,
        "completed_today": completed_today
    }
    
# --- fetch appointment status ---
@router.get("/status-overview", response_model=AppointmentStatusSummary)
async def get_status_overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(receptionist_only)],
):
    today = date.today()

    # takes the status as an input 
    async def get_count(status: AppointmentStatus):
        res = await db.execute(
            select(func.count(Appointment.id)).where(
                and_(Appointment.appointment_date == today, Appointment.status == status)
            )
        )
        return res.scalar() or 0

    return {
        "scheduled": await get_count(AppointmentStatus.SCHEDULED),
        "in_progress": await get_count(AppointmentStatus.IN_PROGRESS),
        "completed": await get_count(AppointmentStatus.COMPLETED),
        "cancelled": await get_count(AppointmentStatus.CANCELLED)
    }
    

# --- fetch the appointments for the day ( with limit constraint) ---
@router.get("/appointments/daily", response_model=List[AppointmentRead])
async def get_daily_appointments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    
    query_date = date.today()

    statement = (
        select(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.doctor),
        )
        .where(Appointment.appointment_date == query_date)
        .order_by(Appointment.appointment_time.asc())
    )

    result = await db.execute(statement)
    return result.scalars().all()
   
    
# --- create a new patient ---
@router.post("/patients", response_model=PatientRead)
async def register_patient(
    patient_in: PatientCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(receptionist_only)]
):
    # check if national_id ot phone number exists 
    result = await db.execute(select(Patient).where(Patient.national_id == patient_in.national_id))
    existing = result.scalars().first()
    
    # if the patient national_ID exists 
    if existing:
        raise HTTPException(status_code=400, detail="Patient already registered with this ID.")

    # fetch the max ID from the database and create one +1
    max_id_res = await db.execute(select(func.max(Patient.display_id)))
    next_id = (max_id_res.scalar() or 0) + 1

    new_patient = Patient(
        full_name=patient_in.full_name,
        national_id=patient_in.national_id,
        email=patient_in.email,
        phone_number=patient_in.phone_number,
        date_of_birth=patient_in.date_of_birth,
        display_id=next_id
    )
    
    db.add(new_patient)
    await db.commit()
    await db.refresh(new_patient)
    return new_patient    

# --- fetch all patients ( search by name, ID, national_ID) ---
@router.get("/patients", response_model=list[PatientRead])
async def search_patients(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(receptionist_only)],
    search: Optional[str] = None,

):  
    # defined the base query 
    query = select(Patient)

    if search:
        
        # search for the given string in any position in the word 
        # ILIKE for case senitivity
        s = f"%{search}%"
        query = query.where(
            or_(
                Patient.full_name.ilike(s),
                Patient.phone_number.ilike(s),
                Patient.national_id.ilike(s),
                cast(Patient.display_id, String).ilike(s)
            )
        )
        

    result = await db.execute(query.order_by(Patient.display_id.desc()))
    return result.scalars().all()    