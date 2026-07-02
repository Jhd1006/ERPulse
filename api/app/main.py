from contextlib import asynccontextmanager
from fastapi import FastAPI
from .routers import hospitals
from .redis_client import close_redis
from .schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()


app = FastAPI(title="ERPulse API", version="0.1.0", lifespan=lifespan)

app.include_router(hospitals.router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health():
    return HealthResponse(status="ok")
