from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID


from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.core.auth import create_access_token, verify_access_token, hash_password, oauth2_scheme, verify_password, admin_only, get_current_user
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
    email = form_data.username.lower()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()


    # if there is no user or password is not verified 
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # if the user is inactive
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")    
    
    # toeken data
    token_data = {
        "sub": str(user.id),
        "role": user.role,       # This identifies the dashboard type
        "name": user.full_name,  # Helpful for displaying the name in the UI header
        "email": user.email
    }    

    token = create_access_token(
       data = token_data,
    expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    return Token(access_token=token, token_type="bearer")

        
# --- get the current user ---
@router.get("/me", response_model=UserPrivate)
async def get_current_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user
        
        
        
    
    