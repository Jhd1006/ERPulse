import asyncio
import httpx
from ..config import settings

_DIRECTIONS_URL = "https://apis-navi.kakaomobility.com/v1/directions"


async def get_duration_sec(
    origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float
) -> int | None:
    """카카오 길찾기 API로 실제 차량 소요시간(초) 조회. 실패 시 None."""
    params = {
        "origin": f"{origin_lng},{origin_lat}",
        "destination": f"{dest_lng},{dest_lat}",
        "summary": "true",
    }
    headers = {"Authorization": f"KakaoAK {settings.KAKAO_REST_API_KEY}"}
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(_DIRECTIONS_URL, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return data["routes"][0]["summary"]["duration"]
    except (httpx.HTTPError, KeyError, IndexError):
        return None


async def rank_by_duration(origin_lat: float, origin_lng: float, candidates: list) -> list:
    """후보 병원들을 실제 소요시간 기준 정렬. 실패한 건 None으로 두고 맨 뒤로 보냄
    (전부 실패하면 안정정렬 특성상 원래 순서=haversine 순서 그대로 유지됨)"""
    durations = await asyncio.gather(*[
        get_duration_sec(origin_lat, origin_lng, h.lat, h.lng) for h in candidates
    ])
    paired = list(zip(candidates, durations))
    paired.sort(key=lambda pair: (pair[1] is None, pair[1]))
    return paired