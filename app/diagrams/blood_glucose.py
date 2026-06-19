from datetime import datetime
from io import BytesIO
from typing import Optional

from app.diagrams.base import Theme, render_single_series
from app.models.blood_glucose import BloodGlucose


def render_chart(
    records: list[BloodGlucose],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    theme: Theme = "light",
) -> BytesIO:
    return render_single_series(
        records,
        title="Blood Glucose",
        ylabel="mmol/L",
        theme=theme,
        start=start,
        end=end,
    )
