from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import func, or_, and_
from sqlmodel import select
from typing import List, Annotated, Optional
from uuid import UUID

from app.models import User, UserRole
from app.schemas.user import UserPrivate, UserCreate, UserRead, UserUpdate
from app.core.auth import admin_only, receptionist_only,  hash_password
from app.api.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# --- Create a new user (ADMIN ONLY) ---
@router.post("/", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(admin_only)],
):
    # check if email exists 
    email = user.email.lower()
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
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


# --- Get all users (ADMIN ONLY) ---
@router.get("/", response_model=List[UserRead])
async def get_all_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(admin_only)],
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

# Fetch all the doctors ( RECEPTIONIST ONLY )
# 
@router.get("/doctors", response_model=List[UserRead])
async def get_doctors(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(receptionist_only)],
):
    doctors = await db.execute(select(User).where(and_(User.role == UserRole.DOCTOR, User.is_active == True)))
    result = doctors.scalars().all()
    return result


# --- Get specific user by ID (ADMIN ONLY) ---
@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(admin_only)],
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


# --- Update a user (ADMIN ONLY) ---
@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(admin_only)],
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Security: prevent admin from demoting themselves
    if user.id == current_user.id and user_in.role is not None:
        if user_in.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Security: You cannot demote yourself from the Admin role"
            )

    # Update fields
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


# --- Deactivate a user (ADMIN ONLY) ---
@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def deactivate_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(admin_only)],
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    # if there is no user with that ID
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # if the user is the current ADMIN
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate yourself")

    # soft delete instead
    user.is_active = False 
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return {"message": f"User {user.full_name} has been deactivated"}


