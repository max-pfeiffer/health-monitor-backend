from datetime import datetime
from io import BytesIO
from typing import Optional

import matplotlib.dates as mdates
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure

from app.models.blood_pressure import BloodPressure


def render_chart(
    records: list[BloodPressure],
    start: Optional[datetime],
    end: Optional[datetime],
    systolic_top: int,
    diastolic_top: int,
    show_systolic: bool,
    show_diastolic: bool,
    show_pulse: bool,
) -> BytesIO:
    fig = Figure(figsize=(12, 5))
    ax = fig.add_subplot(1, 1, 1)

    sns.set_theme(style="ticks")

    if records:
        rows = []
        for r in records:
            ts = r.measured_at
            if show_systolic:
                rows.append(
                    {"measured_at": ts, "value": r.systolic, "metric": "Systolic"}
                )
            if show_diastolic:
                rows.append(
                    {"measured_at": ts, "value": r.diastolic, "metric": "Diastolic"}
                )
            if show_pulse and r.pulse is not None:
                rows.append({"measured_at": ts, "value": r.pulse, "metric": "Pulse"})

        if rows:
            df = pd.DataFrame(rows)
            sns.lineplot(
                data=df,
                x="measured_at",
                y="value",
                hue="metric",
                marker="o",
                markersize=4,
                ax=ax,
            )

    if show_systolic:
        ax.axhline(y=systolic_top, color="red", linewidth=1)
    if show_diastolic:
        ax.axhline(y=diastolic_top, color="purple", linewidth=1)
    ax.set_title("Blood Pressure", fontsize=14, pad=12)
    ax.set_xlabel("Date")
    ax.set_ylabel("mmHg / BPM")

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
