from datetime import datetime
from io import BytesIO
from typing import Optional

import matplotlib.dates as mdates
from matplotlib.figure import Figure

from app.models.blood_glucose import BloodGlucose


def render_chart(
    records: list[BloodGlucose],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> BytesIO:
    fig = Figure(figsize=(10, 4))
    ax = fig.add_subplot(1, 1, 1)

    if records:
        dates = [r.measured_at for r in records]
        values = [float(r.value) for r in records]
        ax.plot(dates, values, marker="o", color="tab:orange")
        fig.autofmt_xdate()

    ax.set_title("Blood Glucose")
    ax.set_xlabel("Date")
    ax.set_ylabel("mmol/L")

    if start is not None or end is not None:
        ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(mdates.AutoDateLocator()))
        xlim = list(ax.get_xlim())
        if start is not None:
            xlim[0] = mdates.date2num(start)
        if end is not None:
            xlim[1] = mdates.date2num(end)
        ax.set_xlim(xlim)
        fig.autofmt_xdate()

    buf = BytesIO()
    fig.savefig(buf, format="svg", bbox_inches="tight")
    buf.seek(0)
    return buf
