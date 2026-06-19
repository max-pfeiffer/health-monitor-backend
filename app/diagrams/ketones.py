from datetime import datetime
from io import BytesIO
from typing import Optional

from app.diagrams.base import Theme, render_single_series
from app.models.ketones import Ketones


def render_chart(
    records: list[Ketones],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    theme: Theme = "light",
) -> BytesIO:
    return render_single_series(
        records,
        title="Ketones",
        ylabel="mmol/L",
        theme=theme,
        start=start,
        end=end,
    )
