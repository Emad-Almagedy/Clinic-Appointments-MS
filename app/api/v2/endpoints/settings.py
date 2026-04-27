from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import select
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, SystemSetting
from app.schemas.settings import SystemSettingRead, SystemSettingUpdate, SystemSettingCreate
from app.core.auth import admin_only
from app.core.cache_config import SettingsCache
from app.api.dependencies import get_db

router = APIRouter()

# --- Get all system settings (ADMIN ONLY) ---
@router.get("/", response_model=dict)
async def get_system_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(admin_only)],
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
        # strip to remove starting and ending spaces, converts to lowercase, replace space with underscore
        category_key = setting.category.strip().lower().replace(" ", "_")

        # if the category is not present create one (new empty list for it)
        if category_key not in grouped_settings:
            grouped_settings[category_key] = []

        # append the setting to the category key associated with it
        grouped_settings[category_key].append(setting)
    
    return grouped_settings

# --- Create a new system setting (ADMIN ONLY) ---
@router.post("/", response_model=SystemSettingRead, status_code=status.HTTP_201_CREATED)
async def create_new_setting(
    setting_in: SystemSettingCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(admin_only)],
):
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == setting_in.key)
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
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

# --- Update a system setting (ADMIN ONLY) ---
@router.patch("/{setting_id}", response_model=SystemSettingRead)
async def update_setting(
    setting_id: int,
    setting_in: SystemSettingUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(admin_only)],
):
    """Update a system setting. Only admins can update settings."""
    result = await db.execute(select(SystemSetting).where(SystemSetting.id == setting_id))
    setting = result.scalars().first()
    
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    
    if setting_in.value is not None:
        setting.value = setting_in.value
        
    db.add(setting)
    await db.commit()
    await db.refresh(setting)
    
    # refresh the JSON file
    await SettingsCache.refresh(db)
    
    return setting

# --- Delete a system setting (ADMIN ONLY) ---
@router.delete("/{setting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(
    setting_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(admin_only)],
):
    result = await db.execute(select(SystemSetting).where(SystemSetting.id == setting_id))
    setting = result.scalars().first()
    
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    
    # Protected core settings
    protected_keys = [
        "appointment_duration",
        "working_hours_start",
        "working_hours_end",
        "max_appointments_per_day",
        "enable_email_notifications",
        "enable_sms_notifications"
    ]
    if setting.key in protected_keys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Cannot delete core system settings required for clinic logic."
        )

    # storing the deleted setting
    deleted_system_setting = SystemSettingRead.model_validate(setting)
    
    await db.delete(setting)
    await db.commit()
    
    # refresh the JSON file
    await SettingsCache.refresh(db)
    
    return deleted_system_setting
