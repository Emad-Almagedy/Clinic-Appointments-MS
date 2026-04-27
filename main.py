from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1.router import api_router
from app.core.cache_config import SettingsCache
from app.api.dependencies import AsyncSessionMaker


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    async with AsyncSessionMaker() as db:
        await SettingsCache.refresh(db)

    yield

    # shutdown (optional cleanup)
    await AsyncSessionMaker().close()


app = FastAPI(lifespan=lifespan)

app.include_router(api_router, prefix="/api/v1")