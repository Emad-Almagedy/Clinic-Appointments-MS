from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import func, or_, cast, String
from sqlmodel import select
from typing import List, Annotated, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Patient, User
from app.schemas.patient import PatientCreate, PatientRead, PatientUpdate
from app.core.auth import receptionist_only
from app.api.v1.dependencies import get_db

router = APIRouter()

# --- Create a new patient (RECEPTIONIST ONLY) ---
@router.post("/", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
async def register_patient(
    patient_in: PatientCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(receptionist_only)],
):
    # check if national_id exists 
    result = await db.execute(select(Patient).where(Patient.national_id == patient_in.national_id))
    existing = result.scalars().first()
    
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient already registered with this national ID.")

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


# --- Get all patients with search (RECEPTIONIST ONLY) ---
@router.get("/", response_model=List[PatientRead])
async def get_patients(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(receptionist_only)],
    search: Optional[str] = None,
):
    query = select(Patient)

    if search:
        # search for the given string in any position in the word 
        # ILIKE for case sensitivity
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


# --- Get specific patient by ID (RECEPTIONIST ONLY) ---
@router.get("/{patient_id}", response_model=PatientRead)
async def get_patient(
    patient_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(receptionist_only)],
):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalars().first()

    # if the patient doesnt exist
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    return patient


# --- Update patient information (RECEPTIONIST ONLY) ---
@router.patch("/{patient_id}", response_model=PatientRead)
async def update_patient(
    patient_id: UUID,
    patient_in: PatientUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(receptionist_only)],
):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalars().first()

    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    # Check if new national_id is already used by another patient ( excluding the patient that we are editing)
    if patient_in.national_id is not None and patient_in.national_id != patient.national_id:
        existing = await db.execute(
            select(Patient).where(
                Patient.national_id == patient_in.national_id,
                Patient.id != patient_id
            )
        )
        if existing.scalars().first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This national ID is already used by another patient.")

    # Update fields if provided
    if patient_in.full_name is not None:
        patient.full_name = patient_in.full_name
    
    if patient_in.national_id is not None:
        patient.national_id = patient_in.national_id
    
    if patient_in.email is not None:
        patient.email = patient_in.email
    
    if patient_in.phone_number is not None:
        patient.phone_number = patient_in.phone_number
    
    if patient_in.date_of_birth is not None:
        patient.date_of_birth = patient_in.date_of_birth

    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    
    return patient


# --- Deactivate patient (SOFT DELETE) (RECEPTIONIST ONLY) ---
@router.delete("/{patient_id}", status_code=status.HTTP_200_OK)
async def deactivate_patient(
    patient_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(receptionist_only)],
):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalars().first()

    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    # Check if patient has any active appointments
    # For now, we'll just deactivate them (soft delete pattern)
    patient.is_active = False
    
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    
    return {"message": f"Patient {patient.full_name} has been deactivated"}
