from datetime import UTC, datetime, timedelta
import jwt
from pwdlib import PasswordHash

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Annotated
import uuid

from app.models import User
from app.core.config import settings

from app.models import User, UserRole
from app.api.dependencies import get_db

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v2/auth/token")


def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    
    if "sub" not in data:
        raise ValueError("Token must include 'sub' (user_id)")
    # takes copy of the user data
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
        
    else:
        # fetches the expire time from the auth.py
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_minutes,
        )
    
    # adds expiration timestamp    
    to_encode.update({"exp": int(expire.timestamp())})
    
    # creates the JWT token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def verify_access_token(token: str) -> str | None:
    """Verify a JWT access token and return the subject (user id) if valid."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            # if not expiration time or user ID then reject immediately
            options={"require": ["exp", "sub"]},
        )
    # if invalide return none    
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    # else extract the sub ( user ID or data)
    else:
        return payload.get("sub")


# --- fetch the current user ---
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = verify_access_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token format")

    # user = await db.get(User, user_uuid)
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

    return user    


# --- Role Based Access Control ---
class RoleChecker:
    def __init__(self, allowed_roles: list[UserRole]):
        # roles allowed for specific endpoint
        self.allowed_roles = allowed_roles
        
    def __call__(self, current_user:User = Depends(get_current_user)): 
        # runs everytime someone tries to open an endpoint
        if current_user.role not in self.allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to perform this action")
        return current_user     
        
admin_only = RoleChecker([UserRole.ADMIN])
doctor_only = RoleChecker([UserRole.DOCTOR])
receptionist_only = RoleChecker([UserRole.RECEPTIONIST])
all_staff = RoleChecker([UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.DOCTOR])    