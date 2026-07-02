from datetime import datetime
from pydantic import BaseModel


class HospitalBase(BaseModel):
    hpid: str
    dutyName: str
    dutyAddr: str | None = None
    dutyTel1: str | None = None
    hvec: int | None = None
    hvoc: int | None = None


class HospitalResponse(HospitalBase):
    id: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0"
