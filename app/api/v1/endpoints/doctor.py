from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List, Optional
from sqlalchemy import func
from sqlmodel import select
from datetime import date
from app.models import User, Appointment, VisitNote, Patient, AppointmentStatus
from app.core.auth import doctor_only
from app.schemas.appointment import DoctorDashboardStats, AppointmentRead, VisitNoteRead, VisitNoteBase, VisitNoteCreate
from app.api.v1.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from uuid import UUID

router = APIRouter()

# --- Dashboard Status ---
@router.get("/status", response_model=DoctorDashboardStats)
async def get_doctor_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_doctor: Annotated[User, Depends(doctor_only)]
):
    # todays appointment countt
    today = date.today()
    today_query = await db.execute(
        select(func.count(Appointment.id))
        .where(Appointment.doctor_id == current_doctor.id)
        .where(Appointment.appointment_date == today)
    )
    todays_count = today_query.scalar() or 0
    
    # upcoming appointments
    upcoming_query = await db.execute(
        select(func.count(Appointment.id))
        .where(Appointment.doctor_id == current_doctor.id)
        .where(Appointment.appointment_date > today)
    )
    upcoming_count = upcoming_query.scalar() or 0
        
    # total patients ( patients treated by the current doctor)
    patient_query = await db.execute(
        select(func.count(func.distinct(Appointment.patient_id)))
        .where(Appointment.doctor_id == current_doctor.id)
    )
    total_patients = patient_query.scalar() or 0
    
    # Total visit notes authored by the current doctor
    notes_query = await db.execute(
        select(func.count(VisitNote.id))
        .where(VisitNote.doctor_id == current_doctor.id)
    )
    notes_count = notes_query.scalar() or 0
    
    return {
        "todays_appointments": todays_count,
        "upcoming_appointments": upcoming_count,
        "total_patients": total_patients,
        "visit_notes_total": notes_count
    }
    
    
# --- Fetch Today's appointments (for the current doctor) ---
@router.get("/appointments/today", response_model=List[AppointmentRead])
async def get_todays_appointments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_doctor: Annotated[User, Depends(doctor_only)]
):
    today = date.today()
    result = await db.execute(
        select(Appointment).options(joinedload(Appointment.patient))
        .where(Appointment.doctor_id == current_doctor.id)
        .where(Appointment.appointment_date == today)
        .order_by(Appointment.appointment_time.asc())
    )
    return result.scalars().all()

# --- Fetch the upcoming appointments( for the current doctor) ---
@router.get("/appointments/upcoming", response_model=List[AppointmentRead])
async def get_upcoming_appointments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_doctor: Annotated[User, Depends(doctor_only)]
):
    today = date.today()
    result = await db.execute(
        select(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.note)
        )
        .where(Appointment.doctor_id == current_doctor.id)
        .where(Appointment.appointment_date > today)
        .order_by(Appointment.appointment_date.asc())
    )
    return result.scalars().all()

# --- view a specific appointment ( for the current doctor )
@router.get("/appointments/{id}", response_model=AppointmentRead)
async def get_appointment_details(
    id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_doctor: Annotated[User, Depends(doctor_only)]
):
    statement = (
        select(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.note)
        )
        .where(Appointment.id == id)
        .where(Appointment.doctor_id == current_doctor.id)
    )
    result = await db.execute(statement=statement)
    appointment = result.scalars().first()
    
    # if there is not appointment with the current id
    if not Appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=" Appointment not found ")
    
    return appointment

# --- update the appointment's notes 
@router.post("/appointments/{id}/notes", response_model=VisitNoteRead)
async def add_visit_note(
    id: UUID,
    input_note: VisitNoteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_doctor: Annotated[User, Depends(doctor_only)]
):
    statement = (
        select(Appointment)
        .where(Appointment.id == id, Appointment.doctor_id == current_doctor.id)
    )
    result = await db.execute(statement=statement)
    appointment = result.scalars().first()
    
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=" Appointment not found ")
    
    # check if note exists
    result = await db.execute(select(VisitNote).where(VisitNote.appointment_id == id))
    note = result.scalars().first()
    
    # if note exists update it 
    if note:
        note.content = input_note.content
        db.add(note)
        await db.commit()
        await db.refresh(note)
        return note
    # if note doesnt exist create a new one 
    new_note = VisitNote(
        content=input_note.content,
        appointment_id=id,
        doctor_id=current_doctor.id
    )
    
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)
    return new_note

# --- fetch all doctor appointments with search and status filter ---
@router.get("/appointments", response_model=List[AppointmentRead])
async def get_doctor_appointments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_doctor: Annotated[User, Depends(doctor_only)],
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
):
    query = (
        select(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.doctor),
            joinedload(Appointment.note),
        )
        .where(Appointment.doctor_id == current_doctor.id)
    )

    if search:
        s = f"%{search}%"
        query = query.where(Appointment.patient.has(Patient.full_name.ilike(s)))

    if status_filter:
        status_enum = next((s for s in AppointmentStatus if s.value.lower() == status_filter.lower()), None)
        if not status_enum:
            raise HTTPException(status_code=400, detail="Invalid status filter")
        query = query.where(Appointment.status == status_enum)

    query = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.asc())

    result = await db.execute(query)
    return result.scalars().all()
        
    





    
    
    