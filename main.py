from fastapi import FastAPI
from app.api.v1.router import api_router_v1
from app.api.v2.router import api_router_v2
from app.core.cache_config import SettingsCache
from app.api.dependencies import AsyncSessionMaker

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    async with AsyncSessionMaker() as db:
        await SettingsCache.refresh(db)

# app.include_router(api_router_v1, prefix="/api/v1")
app.include_router(api_router_v2, prefix="/api/v2" )
