from fastapi import FastAPI
from app.api.v1.router import api_router
from app.core.cache_config import SettingsCache
from app.api.dependencies import AsyncSessionMaker

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    async with AsyncSessionMaker() as db:
        await SettingsCache.refresh(db)

app.include_router(api_router, prefix="/api/v1" )
