from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy import func, or_, and_, cast, String
from sqlmodel import select
from typing import List, Annotated, Optional
from uuid import UUID
from datetime import date, timedelta, time, datetime

from app.models import User, UserRole, Appointment, VisitNote, AppointmentStatus, Patient
from app.schemas.appointment import (
    AppointmentRead, 
    AppointmentCreate, 
    AppointmentUpdate, 
    VisitNoteCreate, 
    VisitNoteRead,
    AppointmentStatusUpdate
)
from app.core.auth import all_staff, admin_only, receptionist_only, doctor_only, get_current_user
from app.api.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from app.core.cache_config import SettingsCache



router = APIRouter()

# --- Get All Appointments (Role-Based) ---
@router.get("/", response_model=List[AppointmentRead])
async def get_appointments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(all_staff)],
    search: Optional[str] = Query(None, description="Search by patient name, patient ID, etc."),
    date: Optional[str] = Query(None, description="'today', 'upcoming', or YYYY-MM-DD"),
    status: Optional[AppointmentStatus] = Query(None, description="Filter by status")
):
    # Eager load relationships for the read schema
    # SQLAlchemy will load related objects automatically in advance, instead of waiting until i access them in the code.
    # so when later i try to access Appointment.patient or Appointment.note no extra queries are triggered
    
    query = select(Appointment).options(
        selectinload(Appointment.patient),
        selectinload(Appointment.note)
    )

    # if the user is a doctor , only his appointments shows up 
    if current_user.role == UserRole.DOCTOR:
        query = query.where(Appointment.doctor_id == current_user.id)
    

    # date filtering 
    today_date = datetime.now().date()
    if date == "today":
        query = query.where(Appointment.appointment_date == today_date)
    elif date == "upcoming":
        query = query.where(Appointment.appointment_date >= today_date)
    elif date:
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.where(Appointment.appointment_date == parsed_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD, 'today', or 'upcoming'.")

    # if status is provided when using the API then filter 
    if status:
        query = query.where(Appointment.status == status)

    # search across the patient field
    if search:
        s = f"%{search}%"
        # We need to join Patient to search its fields
        query = query.join(Appointment.patient).where(
            or_(
                Patient.full_name.ilike(s),
                Patient.national_id.ilike(s),
                # as display_id is not a string column, therefore using cast concider it as a text
                cast(Appointment.display_id, String).ilike(s)
            )
        )

    # Sort by date and time
    query = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
    
    result = await db.execute(query)
    return result.scalars().all()


# --- Get Specific Appointment ---
@router.get("/{appointment_id}", response_model=AppointmentRead)
async def get_appointment(
    appointment_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(all_staff)],
):
    query = select(Appointment).where(Appointment.id == appointment_id).options(
        selectinload(Appointment.patient),
        selectinload(Appointment.note)
    )
    result = await db.execute(query)
    appointment = result.scalars().first()

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    # Doctors can only view their own appointments 
    if current_user.role == UserRole.DOCTOR and appointment.doctor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to view this appointment")

    return appointment


# --- Book Appointment (Receptionist) ---
@router.post("/", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    appointment_in: AppointmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(receptionist_only)],
):
    
    # fetch the clinic settings
    duration_in_minutes = int(SettingsCache.get("appointment_duration"))
    start_working_hours = SettingsCache.get("working_hours_start")
    end_working_hours = SettingsCache.get("working_hours_end")
    max_appointments = int(SettingsCache.get("max_appointments_per_day"))
    clinic_timezone = SettingsCache.get("timezone", "UTC")

    try:
        tz = ZoneInfo(clinic_timezone)
        
    # backup to UTC if error in zone    
    except (ZoneInfoNotFoundError, ValueError):
        tz = ZoneInfo("UTC")
        
    
    # clinic time and appointment time depending on the timezone
    clinic_time_now = datetime.now(tz)    
    new_appointment_time = datetime.combine(appointment_in.appointment_date, appointment_in.appointment_time).replace(tzinfo=tz)
    
    # prevent booking in the past
    if new_appointment_time < clinic_time_now:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cannot book appointments in the past.")
    
    # check working hours 
    work_start = time.fromisoformat(start_working_hours).replace(tzinfo=tz)
    work_end = time.fromisoformat(end_working_hours).replace(tzinfo=tz)
    
    # make sure that the new appointment input time  is aware to match
    new_appointment_aware = appointment_in.appointment_time.replace(tzinfo=tz)
    
    # if the appointment time is before the work start or after the work end
    if not(work_start <= new_appointment_aware < work_end):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Clinic is closed, book between {work_start} and {work_end}")
    
    # check daily limit of appointments 
    daily_count = await db.execute(select(func.count(Appointment.id))
                                   .where(Appointment.appointment_date == appointment_in.appointment_date))
    result = daily_count.scalar() or 0
    
    # if equal or already exceeded
    if result >= max_appointments:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Daily appointment limit reached")
    
    # double booking on a time slot 
    # combine date+time to datetime, add minutes duration, convert back to time 
    new_start = appointment_in.appointment_time
    new_end = (
        datetime.combine(
            appointment_in.appointment_date,
            appointment_in.appointment_time
        ) + timedelta(minutes=duration_in_minutes)
    ).time()
    
    # check if any overlapping appointments (result will have the overlapping appointments)
    result = await db.execute (select(Appointment).where(
    and_(
        Appointment.doctor_id == appointment_in.doctor_id,
        Appointment.appointment_date == appointment_in.appointment_date,
        Appointment.status != AppointmentStatus.CANCELLED,

        # overlap logic
        # does the existing appointment start before our new appointment ends
        # abd does the existing apointment end after our new appointmen starts 
        Appointment.appointment_time < new_end,
        Appointment.appointment_end_time > new_start
    )
    ))
    
    # appointments that are overlapping 
    existing_appointments = result.scalars().first()
    
    if existing_appointments:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor is already booked for this time slot")
    
    max_id_res = await db.execute(select(func.max(Appointment.display_id)))
    next_display_id = (max_id_res.scalar() or 0) + 1
    
    # add the new appointment to the database
    new_appointment = Appointment(
        display_id=next_display_id or 1,
        appointment_date=appointment_in.appointment_date,
        appointment_time=appointment_in.appointment_time,
        appointment_end_time=new_end,
        patient_id=appointment_in.patient_id,
        doctor_id=appointment_in.doctor_id,
        status= appointment_in.status
    )
    
    db.add(new_appointment)
    await db.commit()
    
    # to get the new appointment to display, as we also read data from patient, doctor and note 
    # we need to create a statement with joinedload to prevent missinggreenlet error
    statement = (
        select(Appointment)
        .where(Appointment.id == new_appointment.id)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.doctor),
            joinedload(Appointment.note)  # Matches your AppointmentRead requirements
        )
    )
    fetched_appointment = await db.execute(statement)
    result = fetched_appointment.scalars().first()
    
    return new_appointment


# --- 4. Update Appointment Details (Receptionist) ---
@router.patch("/{appointment_id}", response_model=AppointmentRead)
async def update_appointment(
    id: UUID,
    appointment_in: AppointmentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(receptionist_only)]
):
    # fetch the existing appointment
    result = await db.execute(select(Appointment).where(Appointment.id == id))
    appointment = result.scalars().first()
    
    # if the appointment is not found 
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # fetch the clinic settings
    duration = int(SettingsCache.get("appointment_duration"))
    clinic_timezone = SettingsCache.get("timezone", "UTC")
    
    # check for timezone 
    try:
        tz = ZoneInfo(clinic_timezone)
        
    # backup to UTC if error in zone    
    except (ZoneInfoNotFoundError, ValueError):
        tz = ZoneInfo("UTC")
                                        
    # select if new data or keep the old data
    new_date = appointment_in.appointment_date or appointment.appointment_date
    new_time = appointment_in.appointment_time or appointment.appointment_time
    new_doctor_id = appointment_in.doctor_id or appointment.doctor_id
    
    # if time or doctor changed,  recheck the overlap check
    if appointment_in.appointment_time or appointment_in.appointment_date or appointment_in.doctor_id:
        
        #prevent moving to the past
        clinic_time_now = datetime.now(tz)
        new_appointment_time = datetime.combine(new_date, new_time).replace(tzinfo=tz)
        
        if new_appointment_time.replace(tzinfo=ZoneInfo(clinic_timezone)) < clinic_time_now:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot reschedule to a past time.") 
        
        # not needed the fetch doctors API is already filtering that for me 
        # check if the new doctor is inaactive
        # if appointment_in.doctor_id:
        #     doctor = await db.get(User, new_doctor_id)
        #     if not doctor or not doctor.is_active:
        #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The selected doctor is inactive.")
            
        # calculate the new appointment end time 
        new_start = new_time
        new_end = (new_appointment_time + timedelta(minutes=duration)).timetz()

        # now checking for overlapping appointments
        overlapping_appointments = select(Appointment).where(
            and_(
                Appointment.id != id,  # ignore the current appointment that is being edited
                Appointment.doctor_id == new_doctor_id,
                Appointment.appointment_date == new_date,
                Appointment.status != AppointmentStatus.CANCELLED,
                Appointment.appointment_time < new_end,
                Appointment.appointment_end_time > new_start
            )
        )
        
        result = await db.execute(overlapping_appointments)
        
        # if there is an overlapping appointment 
        if result.scalars().first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The new slot is already booked.")

        # update the end time for creating the new appointment
        appointment.appointment_end_time = new_end

    # 4. Explicitly update the fields
    if appointment_in.appointment_date: appointment.appointment_date = appointment_in.appointment_date
    if appointment_in.appointment_time: appointment.appointment_time = appointment_in.appointment_time
    if appointment_in.doctor_id: appointment.doctor_id = appointment_in.doctor_id
    if appointment_in.status: appointment.status = appointment_in.status

    await db.commit()
    
    # to get the new appointment to display, as we also read data from patient, doctor and note 
    # we need to create a statement with joinedload to prevent missinggreenlet error
    statement = (
        select(Appointment)
        .where(Appointment.id == id)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.doctor),
            joinedload(Appointment.note)
        )
    )
    fetched_appointment = await db.execute(statement)
    result = fetched_appointment.scalars().first()
    return result
