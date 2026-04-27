from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import func, or_, and_
from sqlmodel import select
from typing import List, Annotated, Optional
from uuid import UUID

from app.models import User, UserRole
from app.schemas.user import UserPrivate, UserCreate, UserRead, UserUpdate
from app.core.auth import admin_only, receptionist_only, doctor_only, all_staff, hash_password
from app.api.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession