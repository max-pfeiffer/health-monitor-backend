from datetime import datetime
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class BloodGlucose(SQLModel, table=True):
    __tablename__ = "blood_glucose"
    __table_args__ = (
        sa.UniqueConstraint(
            "user_id", "measured_at", name="uq_blood_glucose_user_measured_at"
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    value: Decimal = Field(
        sa_column=sa.Column(sa.Numeric(precision=5, scale=2), nullable=False)
    )
    measured_at: datetime = Field(index=True)
    notes: Optional[str] = None
