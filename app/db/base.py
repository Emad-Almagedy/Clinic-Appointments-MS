from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Create async engine
engine = create_async_engine(settings.database_url)

async def create_db_and_tables():
    """create all tables defined in the SQLModel schema"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

class Base(DeclarativeBase):
    pass
