import asyncio
from datetime import date, time, datetime
from sqlmodel import select
from datetime import timedelta

# Import all models
from app.models.user import User, UserRole
from app.models.appointment import Appointment, AppointmentStatus, VisitNote
from app.models.patient import Patient

from app.core.auth import hash_password
from app.db.base import create_db_and_tables
from app.api.dependencies import AsyncSessionMaker

async def seed_complete_data() -> None:
    # Alembic manages the tables now so no need of the create_db_and_tables()

    async with AsyncSessionMaker() as db:
        # Seed Users
        users_data = [
            {
                "display_id": 1,
                "full_name": "Admin User",
                "email": "admin@example.com",
                "phone_number": "+1-555-0301",
                "role": UserRole.ADMIN,
                "speciality": None,
                "password": "admin123",
            },
            {
                "display_id": 2,
                "full_name": "Dr. John Smith",
                "email": "john@example.com",
                "phone_number": "+1-555-0101",
                "role": UserRole.DOCTOR,
                "speciality": "Cardiology",
                "password": "doctor123",
            },
            {
                "display_id": 3,
                "full_name": "Dr. Emily Davis",
                "email": "emily@example.com",
                "phone_number": "+1-555-0102",
                "role": UserRole.DOCTOR,
                "speciality": "Pediatrics",
                "password": "doctor123",
            },
            {
                "display_id": 4,
                "full_name": "Sarah Johnson",
                "email": "sarah@example.com",
                "phone_number": "+1-555-0201",
                "role": UserRole.RECEPTIONIST,
                "speciality": None,
                "password": "recep123",
            },
        ]

        users = {}
        for user_data in users_data:
            result = await db.execute(select(User).where(User.email == user_data["email"]))
            user = result.scalars().first()
            if not user:
                user = User(
                    display_id=user_data["display_id"],
                    full_name=user_data["full_name"],
                    email=user_data["email"],
                    phone_number=user_data["phone_number"],
                    role=user_data["role"],
                    speciality=user_data["speciality"],
                    hashed_password=hash_password(user_data["password"]),
                    is_active=True,
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
            users[user_data["email"]] = user

        # Seed Patients
        patients_data = [
            {
                "display_id": 1,
                "full_name": "Alice Brown",
                "national_id": "1234567890",
                "email": "alice.brown@email.com",
                "phone_number": "+1-555-1001",
                "date_of_birth": date(1985, 5, 15),
            },
            {
                "display_id": 2,
                "full_name": "Bob Wilson",
                "national_id": "0987654321",
                "email": "bob.wilson@email.com",
                "phone_number": "+1-555-1002",
                "date_of_birth": date(1990, 8, 22),
            },
            {
                "display_id": 3,
                "full_name": "Charlie Taylor",
                "national_id": "1122334455",
                "email": "charlie.taylor@email.com",
                "phone_number": "+1-555-1003",
                "date_of_birth": date(1975, 12, 10),
            },
        ]

        patients = {}
        for patient_data in patients_data:
            result = await db.execute(select(Patient).where(Patient.national_id == patient_data["national_id"]))
            patient = result.scalars().first()
            if not patient:
                patient = Patient(**patient_data)
                db.add(patient)
                await db.commit()
                await db.refresh(patient)
            patients[patient_data["national_id"]] = patient

        # Seed Appointments
        appointments_data = [
            {
                "display_id": 1,
                "appointment_date": date(2026, 4, 25),
                "appointment_time": time(10, 0),
                "status": AppointmentStatus.SCHEDULED,
                "patient_id": patients["1234567890"].id,
                "doctor_id": users["john@example.com"].id,
            },
            {
                "display_id": 2,
                "appointment_date": date(2026, 4, 26),
                "appointment_time": time(14, 30),
                "status": AppointmentStatus.COMPLETED,
                "patient_id": patients["0987654321"].id,
                "doctor_id": users["emily@example.com"].id,
            },
            {
                "display_id": 3,
                "appointment_date": date(2026, 4, 27),
                "appointment_time": time(9, 0),
                "status": AppointmentStatus.SCHEDULED,
                "patient_id": patients["1122334455"].id,
                "doctor_id": users["john@example.com"].id,
            },
        ]

        appointments = {}
        # We assume a 30-minute duration for seeded data to match your settings
        seed_duration = 30 

        for appt_data in appointments_data:
            # 1. Check if exists
            result = await db.execute(
                select(Appointment).where(
                    Appointment.patient_id == appt_data["patient_id"],
                    Appointment.doctor_id == appt_data["doctor_id"],
                    Appointment.appointment_date == appt_data["appointment_date"],
                    Appointment.appointment_time == appt_data["appointment_time"],
                )
            )
            appt = result.scalars().first()
            
            if not appt:
                # 2. Calculate the end time (This is the critical update!)
                start_dt = datetime.combine(appt_data["appointment_date"], appt_data["appointment_time"])
                end_time = (start_dt + timedelta(minutes=seed_duration)).time()

                # 3. Create with the mandatory appointment_end_time field
                appt = Appointment(
                    appointment_date=appt_data["appointment_date"],
                    appointment_time=appt_data["appointment_time"],
                    appointment_end_time=end_time,
                    status=appt_data["status"],
                    patient_id=appt_data["patient_id"],
                    doctor_id=appt_data["doctor_id"],
                    display_id=appt_data["display_id"]
                )
                
                db.add(appt)
                await db.commit()
                await db.refresh(appt)
            
            appointments[f"{appt_data['patient_id']}_{appt_data['appointment_date']}"] = appt
        
        # Seed Visit Notes
        notes_data = [
            {
                "content": "Patient presented with chest pain. ECG normal. Prescribed rest and follow-up in 2 weeks.",
                "appointment_id": appointments[f"{patients['0987654321'].id}_{date(2026, 4, 26)}"].id,
                "doctor_id": users["emily@example.com"].id,
            },
        ]

        for note_data in notes_data:
            result = await db.execute(select(VisitNote).where(VisitNote.appointment_id == note_data["appointment_id"]))
            note = result.scalars().first()
            if not note:
                note = VisitNote(**note_data)
                db.add(note)
                await db.commit()
                await db.refresh(note)

        print("✅ Complete data seeded successfully")

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_complete_data())
