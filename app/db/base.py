from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine


DATABASE_URL = "sqlite+aiosqlite:///./data/clinic.db"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

async def create_db_and_tables():
    """create all tables defined in the SQLModel schema"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
