import asyncio
from sqlmodel import select

#Import all models so SQLModel can see them
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.appointment import Appointment, VisitNote
from app.models.settings import SystemSetting

from app.core.auth import hash_password
from app.db.base import create_db_and_tables
from app.api.dependencies import AsyncSessionMaker

async def create_admin() -> None:
    # This creates the tables if they don't exist
    await create_db_and_tables()

    async with AsyncSessionMaker() as db:
        # Use .execute() for Async compatibility
        result = await db.execute(select(User).where(User.email == "admin@example.com"))
        admin = result.scalars().first()

        if admin:
            print("ℹ️ Admin already exists:", admin.email)
            return

        admin = User(
            display_id=10,
            full_name="Admin User", # [cite: 256]
            email="admin@example.com", # [cite: 269]
            phone_number="+1-555-0301", # [cite: 269]
            hashed_password=hash_password("admin123"),
            role=UserRole.ADMIN, # [cite: 269]
            is_active=True
        )

        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        print("✅ Admin created successfully")

if __name__ == "__main__":
    asyncio.run(create_admin())