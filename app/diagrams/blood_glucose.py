from datetime import datetime
from io import BytesIO
from typing import Optional

import matplotlib.dates as mdates
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure

from app.models.blood_glucose import BloodGlucose


def render_chart(
    records: list[BloodGlucose],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> BytesIO:
    fig = Figure(figsize=(10, 4))
    ax = fig.add_subplot(1, 1, 1)

    sns.set_theme(style="ticks")

    if records:
        df = pd.DataFrame(
            {"measured_at": r.measured_at, "value": float(r.value)} for r in records
        )
        sns.lineplot(data=df, x="measured_at", y="value", marker="o", ax=ax)

    ax.set_title("Blood Glucose", fontsize=14, pad=12)
    ax.set_xlabel("Date")
    ax.set_ylabel("mmol/L")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    if start is not None or end is not None:
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
