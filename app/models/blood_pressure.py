from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class BloodPressure(SQLModel, table=True):
    __tablename__ = "blood_pressure"

    id: Optional[int] = Field(default=None, primary_key=True)
    systolic: int
    diastolic: int
    pulse: Optional[int] = None
    measured_at: datetime = Field(unique=True, index=True)
    notes: Optional[str] = None
