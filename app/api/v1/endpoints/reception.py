from datetime import date, timedelta, time, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, and_, or_, String, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models import User, Appointment, Patient, AppointmentStatus, UserRole
from app.api.v1.dependencies import get_db
from app.core.auth import get_current_user
from app.core.cache_config import SettingsCache
from app.schemas.user import UserRead
from app.schemas.patient import PatientCreate, PatientRead
from app.schemas.appointment import AppointmentStatusSummary, ReceptionDashboardStats, AppointmentRead, AppointmentCreate, AppointmentUpdate
from app.core.auth import receptionist_only
from typing import Annotated, List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from uuid import UUID
from zoneinfo import ZoneInfo


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
@router.get("/status_overview", response_model=AppointmentStatusSummary)
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
    

# --- fetch the appointments ( all or for the day) ---
@router.get("/appointments_today", response_model=List[AppointmentRead])
async def get_today_appointments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    for_today: Optional[bool] = True
):
    
    statement = (
        select(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.doctor),
            joinedload(Appointment.note)
        )
    )
    
    # check if the timezone settings entered is valid 
    try:
        clinic_timezone = SettingsCache.get("timezone", "UTC")
        tz = ZoneInfo(clinic_timezone)
        
    # backup to UTC if error in zone    
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")
    # if for today filter the ones for the day
    
    if for_today:
        today_date = datetime.now(tz).date()

        statement = statement.where(
            Appointment.appointment_date == today_date
        )

        statement = statement.order_by(
            Appointment.appointment_time.asc()
     )
    else:
        statement = statement.order_by(
            Appointment.appointment_date.desc(),
            Appointment.appointment_time.desc()
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
    next_display_id = (max_id_res.scalar() or 0) + 1

    new_patient = Patient(
        full_name=patient_in.full_name,
        national_id=patient_in.national_id,
        email=patient_in.email,
        phone_number=patient_in.phone_number,
        date_of_birth=patient_in.date_of_birth,
        display_id=next_display_id,
    )
    
    db.add(new_patient)
    await db.commit()
    await db.refresh(new_patient)
    return new_patient    

# --- fetch all patients ( search by name, ID, national_ID) ---
@router.get("/patients", response_model=list[PatientRead])
async def get_patients(
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

# --- fetch all the doctors ---
@router.get("/doctors", response_model=List[UserRead])
async def get_doctors(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(receptionist_only)],
):
    doctors = await db.execute(select(User).where(and_(User.role == UserRole.DOCTOR, User.is_active == True)))
    result = doctors.scalars().all()
    return result

# --- book appointments ---
@router.post("/appointments", response_model=AppointmentRead)
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

# --- update an appointment ---    
@router.patch("/appointments/{id}", response_model=AppointmentRead)
async def reschedule_appointment(
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
