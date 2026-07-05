from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)

# 커넥션 풀 수정
# engine = create_async_engine(
#     settings.DATABASE_URL,
#     echo=False,
#     pool_size=10,
#     max_overflow=10,
#     pool_timeout=30,
# )

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as session:
        yield session
