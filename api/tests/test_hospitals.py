from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import Hospital
from app.database import get_db
from app.redis_client import get_redis

client = TestClient(app)


class FakeScalars:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class FakeResult:
    def __init__(self, items=None, one=None):
        self._items = items or []
        self._one = one

    def scalars(self):
        return FakeScalars(self._items)

    def scalar_one_or_none(self):
        return self._one


def make_hospital(**overrides):
    defaults = dict(
        id=1,
        hpid="A001",
        dutyName="테스트병원",
        dutyAddr="서울시 어딘가",
        dutyTel1="02-1234-5678",
        hvec=3,
        hvoc=1,
        updated_at=datetime.utcnow(),
    )
    defaults.update(overrides)
    return Hospital(**defaults)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_list_hospitals_returns_items_from_db():
    fake_db = AsyncMock()
    fake_db.execute.return_value = FakeResult(items=[make_hospital()])
    app.dependency_overrides[get_db] = lambda: fake_db

    response = client.get("/hospitals/")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["hpid"] == "A001"


def test_get_hospital_found_returns_200():
    fake_db = AsyncMock()
    fake_db.execute.return_value = FakeResult(one=make_hospital(hpid="A002"))
    app.dependency_overrides[get_db] = lambda: fake_db

    response = client.get("/hospitals/A002")

    assert response.status_code == 200
    assert response.json()["hpid"] == "A002"


def test_get_hospital_not_found_returns_404():
    fake_db = AsyncMock()
    fake_db.execute.return_value = FakeResult(one=None)
    app.dependency_overrides[get_db] = lambda: fake_db

    response = client.get("/hospitals/NOPE")

    assert response.status_code == 404


def test_collect_calls_sync_to_db(monkeypatch):
    fake_db = AsyncMock()
    app.dependency_overrides[get_db] = lambda: fake_db

    fake_sync = AsyncMock(return_value=5)
    monkeypatch.setattr("app.routers.hospitals.sync_to_db", fake_sync)

    response = client.post("/hospitals/collect")

    assert response.status_code == 200
    assert response.json() == {"synced": 5}
    fake_sync.assert_called_once_with(fake_db)


def test_realtime_uses_fallback(monkeypatch):
    app.dependency_overrides[get_redis] = lambda: AsyncMock()

    fake_fallback = AsyncMock(return_value=([{"hpid": "A001", "hvec": 2}], True))
    monkeypatch.setattr("app.routers.hospitals.get_with_fallback", fake_fallback)

    response = client.get("/hospitals/realtime")

    assert response.status_code == 200
    body = response.json()
    assert body["from_cache"] is True
    assert body["items"] == [{"hpid": "A001", "hvec": 2}]