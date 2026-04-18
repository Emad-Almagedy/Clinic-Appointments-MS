import uuid
from uuid import UUID
from typing import Optional
from sqlmodel import SQLModel, Field

class SystemSetting(SQLModel, table=True):
    id: int = Field(default=None, sa_column_kwargs={"autoincrement": True}, index=True, unique=True, primary_key=True)
    key: str = Field(unique=True, index=True) 
    value: str 
    category: Optional[str] = None 