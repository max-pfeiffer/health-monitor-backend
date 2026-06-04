from datetime import datetime
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class Ketones(SQLModel, table=True):
    __tablename__ = "ketones"

    id: Optional[int] = Field(default=None, primary_key=True)
    value: Decimal = Field(
        sa_column=sa.Column(sa.Numeric(precision=5, scale=2), nullable=False)
    )
    measured_at: datetime
    notes: Optional[str] = None
