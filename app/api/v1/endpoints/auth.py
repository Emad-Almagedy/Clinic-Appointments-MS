from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID


from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from app import models

from app.core.auth import create_access_token, verify_access_token, hash_password, oauth2_scheme, verify_password, admin_only
from app.api.v1.dependencies import get_db
from app.core.config import settings
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserUpdate, UserPrivate, UserPublic

from app.models import User, UserRole

router = APIRouter()


# --- login logic ---
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.email.ilike(form_data.username)))
    user = result.scalars().first()


    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    return Token(access_token=token, token_type="bearer", role = user.role)

# --- Create a user ---
@router.post("/users", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(admin_only)],
):
    # check if email exists 
    email = user.email.lower()
    result = await db.execute(select(User).where(User.email.ilike(email)))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already Registered")
    
    new_user = models.User(
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
        
        
    
    