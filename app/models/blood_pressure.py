from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class BloodPressure(SQLModel, table=True):
    __tablename__ = "blood_pressure"
    __table_args__ = (
        sa.UniqueConstraint(
            "user_id", "measured_at", name="uq_blood_pressure_user_measured_at"
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    systolic: int
    diastolic: int
    pulse: Optional[int] = None
    measured_at: datetime = Field(index=True)
    notes: Optional[str] = None
