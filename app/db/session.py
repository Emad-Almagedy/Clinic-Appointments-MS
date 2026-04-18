from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

from .base import engine

# async session maker 
AsyncSessionMaker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
