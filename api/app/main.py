from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import hospitals, cpu
from .redis_client import close_redis
from .schemas import HealthResponse
from prometheus_fastapi_instrumentator import Instrumentator

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()

app = FastAPI(title="ERPulse API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(hospitals.router)
app.include_router(cpu.router)
Instrumentator(excluded_handlers=["/metrics", "/health"]).instrument(app, latency_lowr_buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5)).expose(app, include_in_schema=False)

@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health():
    return HealthResponse(status="ok")