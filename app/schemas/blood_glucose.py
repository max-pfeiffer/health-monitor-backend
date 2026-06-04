from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel


class BloodGlucoseBase(SQLModel):
    value: Decimal
    measured_at: datetime
    notes: Optional[str] = None


class BloodGlucoseCreate(BloodGlucoseBase):
    pass


class BloodGlucoseUpdate(SQLModel):
    value: Optional[Decimal] = None
    measured_at: Optional[datetime] = None
    notes: Optional[str] = None


class BloodGlucoseRead(BloodGlucoseBase):
    id: int
