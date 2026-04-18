from app.db.session import AsyncSessionMaker
from sqlalchemy.ext.asyncio import AsyncSession

# Get DB session 
async def get_db() -> AsyncSession:
    async with AsyncSessionMaker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()    