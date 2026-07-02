from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis

from ..database import get_db
from ..models import Hospital
from ..schemas import HospitalResponse
from ..redis_client import get_redis
from ..services.collector import fetch_er_realtime, sync_to_db
from ..services.fallback import get_with_fallback

router = APIRouter(prefix="/hospitals", tags=["hospitals"])


@router.get("/", response_model=list[HospitalResponse])
async def list_hospitals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Hospital).order_by(Hospital.dutyName))
    return result.scalars().all()


@router.post("/collect")
async def collect(db: AsyncSession = Depends(get_db)):
    """공공 API에서 응급실 목록을 수집해 DB에 upsert"""
    count = await sync_to_db(db)
    return {"synced": count}


@router.get("/realtime")
async def realtime_er_status(redis: Redis = Depends(get_redis)):
    """공공 API 실시간 응급실 가용 병상 (Redis fallback 적용)"""
    data, from_cache = await get_with_fallback(redis, fetch_er_realtime)
    return {"from_cache": from_cache, "items": data}


@router.get("/{hpid}", response_model=HospitalResponse)
async def get_hospital(hpid: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Hospital).where(Hospital.hpid == hpid))
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital
