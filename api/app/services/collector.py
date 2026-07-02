import httpx
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from ..config import settings
from ..models import Hospital

# 공공데이터포털 응급의료정보 API (data.go.kr > B552657/ErmctInfoInqireService)
_ER_LIST_ENDPOINT = "/getEgytListInfoInqire"
_ER_REALTIME_ENDPOINT = "/getEmrrmRltmUsefulSckbdInfoInqire"


async def fetch_er_list() -> list[dict]:
    """응급실 목록 조회 (기본 정보: 병원명, 주소, 전화번호)"""
    url = f"{settings.PUBLIC_API_BASE_URL}{_ER_LIST_ENDPOINT}"
    params = {
        "serviceKey": settings.PUBLIC_API_KEY,
        "pageNo": 1,
        "numOfRows": 200,
        "_type": "json",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    items = (
        data.get("response", {})
        .get("body", {})
        .get("items", {})
        .get("item", [])
    )
    return items if isinstance(items, list) else [items]


async def fetch_er_realtime() -> list[dict]:
    """실시간 응급실 가용 병상 정보 조회"""
    url = f"{settings.PUBLIC_API_BASE_URL}{_ER_REALTIME_ENDPOINT}"
    params = {
        "serviceKey": settings.PUBLIC_API_KEY,
        "pageNo": 1,
        "numOfRows": 200,
        "_type": "json",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    items = (
        data.get("response", {})
        .get("body", {})
        .get("items", {})
        .get("item", [])
    )
    return items if isinstance(items, list) else [items]


async def sync_to_db(db: AsyncSession) -> int:
    items = await fetch_er_list()

    for item in items:
        tel = item.get("dutyTel1")
        stmt = insert(Hospital).values(
            hpid=item.get("hpid"),
            dutyName=item.get("dutyName"),
            dutyAddr=item.get("dutyAddr"),
            dutyTel1=str(tel) if tel is not None else None,
            hvec=item.get("hvec"),
            hvoc=item.get("hvoc"),
        ).on_conflict_do_update(
            index_elements=["hpid"],
            set_={
                "dutyName": item.get("dutyName"),
                "dutyAddr": item.get("dutyAddr"),
                "dutyTel1": str(tel) if tel is not None else None,
                "hvec": item.get("hvec"),
                "hvoc": item.get("hvoc"),
                "updated_at": func.now(),
            }
        )
        await db.execute(stmt)

    await db.commit()
    return len(items)
