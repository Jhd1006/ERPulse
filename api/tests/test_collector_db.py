import os
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.database import Base
from app.models import Hospital
from app.services.collector import sync_to_db

pytestmark = pytest.mark.asyncio(loop_scope="module")

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://erpulse:erpulse@localhost:5432/erpulse",
)
TEST_HPID = "TEST-COLLECTOR-001"

test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(loop_scope="module")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with TestSessionLocal() as cleanup:
        await cleanup.execute(delete(Hospital).where(Hospital.hpid == TEST_HPID))
        await cleanup.commit()


async def test_sync_to_db_inserts_new_hospital(db_session, monkeypatch):
    fake_items = [{
        "hpid": TEST_HPID,
        "dutyName": "최초등록병원",
        "dutyAddr": "서울시 A구",
        "dutyTel1": 21234567,
        "hvec": 5,
        "hvoc": 2,
    }]
    monkeypatch.setattr(
        "app.services.collector.fetch_er_list",
        AsyncMock(return_value=fake_items),
    )

    count = await sync_to_db(db_session)
    assert count == 1
    result = await db_session.execute(select(Hospital).where(Hospital.hpid == TEST_HPID))
    hospital = result.scalar_one()
    assert hospital.dutyName == "최초등록병원"
    assert hospital.dutyTel1 == "21234567"


async def test_sync_to_db_upserts_existing_hospital(db_session, monkeypatch):
    first_batch = [{
        "hpid": TEST_HPID,
        "dutyName": "최초등록병원",
        "dutyAddr": "서울시 A구",
        "dutyTel1": "02-1111-1111",
        "hvec": 5,
        "hvoc": 2,
    }]
    monkeypatch.setattr(
        "app.services.collector.fetch_er_list",
        AsyncMock(return_value=first_batch),
    )
    await sync_to_db(db_session)

    updated_batch = [{
        "hpid": TEST_HPID,
        "dutyName": "이름변경병원",
        "dutyAddr": "서울시 A구",
        "dutyTel1": "02-1111-1111",
        "hvec": 1,
        "hvoc": 0,
    }]
    monkeypatch.setattr(
        "app.services.collector.fetch_er_list",
        AsyncMock(return_value=updated_batch),
    )
    count = await sync_to_db(db_session)

    assert count == 1
    result = await db_session.execute(select(Hospital).where(Hospital.hpid == TEST_HPID))
    hospital = result.scalar_one()
    assert hospital.dutyName == "이름변경병원"
    assert hospital.hvec == 1