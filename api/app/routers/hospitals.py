import math

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


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


@router.get("/nearest", response_model=list[HospitalResponse])
async def nearest_hospitals(
    lat: float, lng: float, limit: int = 5, db: AsyncSession = Depends(get_db)
):
    """가용 병상이 있는 응급실을 좌표 기준 가까운 순으로 조회 (결정론적 haversine 계산)"""
    result = await db.execute(
        select(Hospital).where(
            Hospital.lat.is_not(None), Hospital.lng.is_not(None), Hospital.hvec > 0
        )
    )
    candidates = result.scalars().all()
    with_distance = [
        (h, round(_haversine_km(lat, lng, h.lat, h.lng), 2)) for h in candidates
    ]
    with_distance.sort(key=lambda pair: pair[1])
    return [
        HospitalResponse.model_validate(h, from_attributes=True).model_copy(
            update={"distance_km": dist}
        )
        for h, dist in with_distance[:limit]
    ]


@router.get("/{hpid}", response_model=HospitalResponse)
async def get_hospital(hpid: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Hospital).where(Hospital.hpid == hpid))
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital