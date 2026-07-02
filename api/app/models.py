from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hpid: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    dutyName: Mapped[str] = mapped_column(String(100), nullable=False)
    dutyAddr: Mapped[str | None] = mapped_column(String(200))
    dutyTel1: Mapped[str | None] = mapped_column(String(20))
    hvec: Mapped[int | None] = mapped_column(Integer)   # 응급실 가용 병상 수
    hvoc: Mapped[int | None] = mapped_column(Integer)   # 수술실 가용 수
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
