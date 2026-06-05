from datetime import datetime
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class BloodGlucose(SQLModel, table=True):
    __tablename__ = "blood_glucose"

    id: Optional[int] = Field(default=None, primary_key=True)
    value: Decimal = Field(
        sa_column=sa.Column(sa.Numeric(precision=5, scale=2), nullable=False)
    )
    measured_at: datetime = Field(unique=True, index=True)
    notes: Optional[str] = None
