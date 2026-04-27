from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy import func
from typing import Annotated
from datetime import datetime, timedelta

from app.models import User, UserRole, Appointment, Patient, VisitNote, AppointmentStatus
from app.core.auth import get_current_user
from app.api.dependencies import get_db
from app.schemas.appointment import AdminDashboardStats, DoctorDashboardStats, ReceptionDashboardStats, AppointmentStatusSummary

router = APIRouter()

@router.get("/")
async def get_dashboard_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    today = datetime.now().date()
    
    if current_user.role == UserRole.ADMIN:
        total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
        total_doctors = (await db.execute(select(func.count(User.id)).where(User.role == UserRole.DOCTOR))).scalar() or 0
        total_patients = (await db.execute(select(func.count(Patient.id)))).scalar() or 0
        total_appointments = (await db.execute(select(func.count(Appointment.id)))).scalar() or 0
        
        scheduled = (await db.execute(select(func.count(Appointment.id)).where(Appointment.status == AppointmentStatus.SCHEDULED))).scalar() or 0
        in_progress = (await db.execute(select(func.count(Appointment.id)).where(Appointment.status == AppointmentStatus.IN_PROGRESS))).scalar() or 0
        completed = (await db.execute(select(func.count(Appointment.id)).where(Appointment.status == AppointmentStatus.COMPLETED))).scalar() or 0
        cancelled = (await db.execute(select(func.count(Appointment.id)).where(Appointment.status == AppointmentStatus.CANCELLED))).scalar() or 0

        return AdminDashboardStats(
            total_users=total_users,
            total_doctors=total_doctors,
            total_patients=total_patients,
            total_appointments=total_appointments,
            status_summary=AppointmentStatusSummary(
                scheduled=scheduled,
                in_progress=in_progress,
                completed=completed,
                cancelled=cancelled
            )
        )
        
    elif current_user.role == UserRole.DOCTOR:
        todays_appointments = (await db.execute(select(func.count(Appointment.id)).where(
            Appointment.doctor_id == current_user.id,
            Appointment.appointment_date == today
        ))).scalar() or 0
        
        upcoming_appointments = (await db.execute(select(func.count(Appointment.id)).where(
            Appointment.doctor_id == current_user.id,
            Appointment.appointment_date >= today
        ))).scalar() or 0
        
        # Total distinct patients for this doctor based on appointments
        total_patients = (await db.execute(select(func.count(func.distinct(Appointment.patient_id))).where(
            Appointment.doctor_id == current_user.id
        ))).scalar() or 0
        
        visit_notes_total = (await db.execute(select(func.count(VisitNote.id)).where(
            VisitNote.doctor_id == current_user.id
        ))).scalar() or 0
        
        return DoctorDashboardStats(
            todays_appointments=todays_appointments,
            upcoming_appointments=upcoming_appointments,
            total_patients=total_patients,
            visit_notes_total=visit_notes_total
        )
        
    elif current_user.role == UserRole.RECEPTIONIST:
        todays_appointments = (await db.execute(select(func.count(Appointment.id)).where(
            Appointment.appointment_date == today
        ))).scalar() or 0
        
        upcoming_7_days = (await db.execute(select(func.count(Appointment.id)).where(
            Appointment.appointment_date >= today,
            Appointment.appointment_date <= today + timedelta(days=7)
        ))).scalar() or 0
        
        total_patients = (await db.execute(select(func.count(Patient.id)))).scalar() or 0
        
        scheduled_today = (await db.execute(select(func.count(Appointment.id)).where(
            Appointment.appointment_date == today,
            Appointment.status == AppointmentStatus.SCHEDULED
        ))).scalar() or 0
        in_progress_today = (await db.execute(select(func.count(Appointment.id)).where(
            Appointment.appointment_date == today,
            Appointment.status == AppointmentStatus.IN_PROGRESS
        ))).scalar() or 0
        completed_today = (await db.execute(select(func.count(Appointment.id)).where(
            Appointment.appointment_date == today,
            Appointment.status == AppointmentStatus.COMPLETED
        ))).scalar() or 0
        cancelled_today = (await db.execute(select(func.count(Appointment.id)).where(
            Appointment.appointment_date == today,
            Appointment.status == AppointmentStatus.CANCELLED
        ))).scalar() or 0
        
        return ReceptionDashboardStats(
            todays_appointments=todays_appointments,
            upcoming_7_days=upcoming_7_days,
            total_patients=total_patients,
            completed_today=completed_today,
            status_summary=AppointmentStatusSummary(
                scheduled=scheduled_today,
                in_progress=in_progress_today,
                completed=completed_today,
                cancelled=cancelled_today
            )
        )
