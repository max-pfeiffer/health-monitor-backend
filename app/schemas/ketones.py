from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel


class KetonesBase(SQLModel):
    value: Decimal
    measured_at: datetime
    notes: Optional[str] = None


class KetonesCreate(KetonesBase):
    pass


class KetonesUpdate(SQLModel):
    value: Optional[Decimal] = None
    measured_at: Optional[datetime] = None
    notes: Optional[str] = None


class KetonesRead(KetonesBase):
    id: int
