import asyncio
from sqlmodel import select

from app.models.settings import SystemSetting
from app.db.base import create_db_and_tables
from app.api.dependencies import AsyncSessionMaker

SETTINGS_TO_SEED = [
    # Clinic Information
    {"key": "clinic_name", "value": "City Medical Clinic", "category": "Clinic Information"},
    {"key": "clinic_address", "value": "123 Healthcare Ave, Medical District", "category": "Clinic Information"},
    {"key": "clinic_phone", "value": "+1-555-CLINIC", "category": "Clinic Information"},
    {"key": "clinic_email", "value": "info@citymedicalclinic.com", "category": "Clinic Information"},

    # Appointment Settings
    {"key": "appointment_duration", "value": "30", "category": "Appointment Settings"},
    {"key": "working_hours_start", "value": "08:00", "category": "Appointment Settings"},
    {"key": "working_hours_end", "value": "18:00", "category": "Appointment Settings"},
    {"key": "max_appointments_per_day", "value": "20", "category": "Appointment Settings"},

    # System Settings
    {"key": "timezone", "value": "America/New_York", "category": "System Settings"},
    {"key": "enable_email_notifications", "value": "true", "category": "System Settings"},
    {"key": "enable_sms_notifications", "value": "false", "category": "System Settings"},
]


async def seed_system_settings() -> None:
    # Alembic manages the tables now so no need of the create_db_and_tables()
    
    async with AsyncSessionMaker() as db:
        created = 0
        updated = 0

        for setting_data in SETTINGS_TO_SEED:
            result = await db.execute(select(SystemSetting).where(SystemSetting.key == setting_data["key"]))
            existing_setting = result.scalars().first()

            if existing_setting:
                existing_setting.value = setting_data["value"]
                existing_setting.category = setting_data["category"]
                updated += 1
            else:
                new_setting = SystemSetting(
                    key=setting_data["key"],
                    value=setting_data["value"],
                    category=setting_data["category"],
                )
                db.add(new_setting)
                created += 1

        if created or updated:
            await db.commit()

    print(f"✅ System settings seeded: {created} created, {updated} updated")


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_system_settings())
