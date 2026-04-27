from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import func, or_, cast, String
from sqlmodel import select
from sqlalchemy.orm import joinedload
from typing import List, Annotated, Optional
from app.models import User, Appointment, Patient, UserRole, AppointmentStatus, SystemSetting
from app.models import SystemSetting
from app.schemas.user import  UserPrivate, UserCreate, UserRead, UserUpdate
from app.schemas.appointment import AppointmentRead, AppointmentStatusSummary, AdminDashboardStats
from app.schemas.settings import SystemSettingRead, SystemSettingUpdate, SystemSettingCreate
from app.core.auth import admin_only
from app.core.cache_config import SettingsCache
from app.api.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.auth import hash_password

router = APIRouter()

# --- admin Dashboard stats ---
@router.get("/stats", response_model=AdminDashboardStats)
async def get_admin_stats(
  db: Annotated[AsyncSession, Depends(get_db)],
  current_admin: Annotated[User, Depends(admin_only)]  
):
    user_count = await db.execute(select(func.count(User.id)))
    doctor_count = await db.execute(select(func.count(User.id)).where(User.role == UserRole.DOCTOR))
    patient_count = await db.execute(select(func.count(Patient.id)))
    appointment_count = await db.execute(select(func.count(Appointment.id)))
    
    return {
        "total_users": user_count.scalar() or 0,
        "total_doctors": doctor_count.scalar() or 0,
        "total_patients": patient_count.scalar() or 0,
        "total_appointments": appointment_count.scalar() or 0,
    }
    
# --- Appointment Status summary ---
@router.get("/status_summary", response_model=AppointmentStatusSummary)   
async def get_admin_status_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_admin: Annotated[User, Depends(admin_only)]
): 
    result = await db.execute(
        select(Appointment.status, func.count(Appointment.id))
        .group_by(Appointment.status)
    )
    status_counts = dict(result.all())
    
    return {
        "scheduled": status_counts.get(AppointmentStatus.SCHEDULED, 0),
        "in_progress": status_counts.get(AppointmentStatus.IN_PROGRESS, 0),
        "completed": status_counts.get(AppointmentStatus.COMPLETED, 0),
        "cancelled": status_counts.get(AppointmentStatus.CANCELLED, 0)
    }


# --- Fetch all the appointments ---
@router.get("/appointments", response_model=List[AppointmentRead])
async def get_all_appointments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_admin: Annotated[User, Depends(admin_only)],
    search: Optional[str] = None,
    limit: Optional[int] = None,
):
    statement =(
        select(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.doctor),
            joinedload(Appointment.note) 
            )
    )

    if search:
        s = f"%{search}%"
        statement = statement.where(
            or_(
                Appointment.patient.has(Patient.full_name.ilike(s)),
                Appointment.doctor.has(User.full_name.ilike(s)),
                cast(Appointment.display_id, String).ilike(s)
            )
        )

    statement = statement.order_by(Appointment.created_at.desc())
    
    # if there is a limit apply it else return all appointments
    if limit is not None:
        statement = statement.limit(limit)
    
    result = await db.execute(statement)    
    return result.scalars().all()

# --- Create a new user ---
@router.post("/users", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_admin: Annotated[User, Depends(admin_only)],
):
    # check if email exists 
    email = user.email.lower()
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already Registered")
    
    result = await db.execute(select(func.max(User.display_id)))
    max_display_id = result.scalar() or 0
    
    new_user = User(
        display_id=max_display_id + 1,
        full_name=user.full_name,
        email=email,
        phone_number=user.phone_number,
        role=user.role,
        speciality=user.speciality if user.role == UserRole.DOCTOR else None,
        hashed_password=hash_password(user.password),
        is_active=user.is_active,
    )
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except Exception:
        await db.rollback()
        raise
            
    return new_user    

# --- Fetch all the users ---
@router.get("/users", response_model=List[UserRead])
async def get_all_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_admin: Annotated[User, Depends(admin_only)],
    search: Optional[str] = None,
):
    query = select(User)

    if search:
        s = f"%{search}%"
        query = query.where(
            or_(
                User.full_name.ilike(s),
                User.email.ilike(s),
                User.phone_number.ilike(s)
            )
        )

    result = await db.execute(query.order_by(User.display_id.asc()))
    return result.scalars().all()

# --- Update a user ---
@router.patch("/users/{id}", response_model=UserRead)
async def update_user(
    id: UUID,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(admin_only)
):
    
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == current_admin.id and user_in.role is not None:
        if user_in.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Security: You cannot demote yourself from the Admin role.")

    if user_in.full_name is not None:
        user.full_name = user_in.full_name 
    
    if user_in.email is not None:
        user.email = user_in.email 
        
    if user_in.phone_number is not None:
        user.phone_number = user_in.phone_number 
        
    if user_in.role is not None:
        user.role = user_in.role 
        
    if user_in.speciality is not None:
        user.speciality = user_in.speciality 
        
    if user_in.is_active is not None:
        user.is_active = user_in.is_active

    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user

# --- Delete a User (Soft Delete) ---
@router.delete("/users/{id}", status_code=status.HTTP_200_OK) 
async def deactivate_user(
    id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_admin: Annotated[User, Depends(admin_only)],
):
    
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cannot deactivate yourself.")

    # soft delete instead
    user.is_active = False 
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return {"message": f"User {user.full_name} has been deactivated."}

# --- fetch the system settings ---
@router.get("/settings", response_model=dict)
async def get_system_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_admin: Annotated[User, Depends(admin_only)],
):
    
    result = await db.execute(select(SystemSetting))
    settings = result.scalars().all()

    # sort by category
    grouped_settings = {
        "clinic_information": [],
        "appointment_settings": [],
        "system_settings": []
    }
    
    for setting in settings:
        # strip to remove starting and ending spaces, converts to lowercase, replace space with undrescore
        category_key = setting.category.strip().lower().replace(" ", "_")

        # if the category is not present create one ( new empty list for it )
        if category_key not in grouped_settings:
            grouped_settings[category_key] = []

        # append the setting to the category key assosiated wit it
        grouped_settings[category_key].append(setting)
    
    return grouped_settings

# --- create a system setting ---
@router.post("/settings", response_model=SystemSettingRead, status_code=status.HTTP_201_CREATED)
async def create_new_setting(
    setting_in: SystemSettingCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_admin: Annotated[User, Depends(admin_only)]
):
    
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == setting_in.key)
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=400, 
            detail=f"Setting with key '{setting_in.key}' already exists."
        )

    # Basic explicit assignment
    new_setting = SystemSetting(
        key=setting_in.key,
        value=setting_in.value,
        category=setting_in.category,
    )
    
    db.add(new_setting)
    await db.commit()
    await db.refresh(new_setting)
    
    # refresh the JSON file
    await SettingsCache.refresh(db)
    
    return new_setting

# --- update a system setting ---
@router.patch("/settings/{id}", response_model=SystemSettingRead)
async def update_setting(
    id: int,
    setting_in: SystemSettingUpdate,
    db: Annotated[AsyncSession , Depends(get_db)],
    current_admin: Annotated[User, Depends(admin_only)]
):
   
    result = await db.execute(select(SystemSetting).where(SystemSetting.id == id))
    setting = result.scalars().first()
    
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    if setting_in.value is not None:
        setting.value = setting_in.value
        
    db.add(setting)
    await db.commit()
    await db.refresh(setting)
    
    # refresh the JSON file
    await SettingsCache.refresh(db)
    
    return setting

# --- delete a system setting ---
@router.delete("/settings/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(
    id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_admin: Annotated[User, Depends(admin_only)]
):
    
    result = await db.execute(select(SystemSetting).where(SystemSetting.id == id))
    setting = result.scalars().first()
    
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    protected_keys = [
        "appointment_duration",
        "working_hours_start",
        "working_hours_end",
        "max_appointments_per_day",
        "enable_email_notifications",
        "enable_sms_notifications"
        ]
    if setting.key in protected_keys:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete core system settings required for clinic logic.")

    # storing the deleted to be deleted
    deleted_system_setting = SystemSettingRead.model_validate(setting)
    
    await db.delete(setting)
    await db.commit()
    
    # refresh the JSON file
    await SettingsCache.refresh(db)
    
    return deleted_system_setting