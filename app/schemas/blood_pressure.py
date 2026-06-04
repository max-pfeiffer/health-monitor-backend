from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel


class BloodPressureBase(SQLModel):
    systolic: int
    diastolic: int
    pulse: Optional[int] = None
    measured_at: datetime
    notes: Optional[str] = None


class BloodPressureCreate(BloodPressureBase):
    pass


class BloodPressureUpdate(SQLModel):
    systolic: Optional[int] = None
    diastolic: Optional[int] = None
    pulse: Optional[int] = None
    measured_at: Optional[datetime] = None
    notes: Optional[str] = None


class BloodPressureRead(BloodPressureBase):
    id: int
