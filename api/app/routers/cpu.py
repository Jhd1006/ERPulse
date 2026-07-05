from fastapi import APIRouter

router = APIRouter(prefix="/cpu", tags=["cpu"])


@router.get("/stress")
async def cpu_stress():
    """HPA CPU 스케일링 검증용 - 순수 연산 부하 (DB/Redis 미사용)"""
    total = 0
    for i in range(10_000_000):
        total += i * i
    return {"result": total}

