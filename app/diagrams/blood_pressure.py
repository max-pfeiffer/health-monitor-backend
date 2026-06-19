from datetime import datetime
from io import BytesIO
from typing import Optional

import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure

from app.diagrams.base import (
    Theme,
    _style,
    apply_time_axis,
    reference_color,
    to_svg,
)
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
    theme: Theme = "light",
) -> BytesIO:
    title = "Blood Pressure"
    with _style(theme):
        fig = Figure(figsize=(12, 5))
        ax = fig.add_subplot(1, 1, 1)

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
                    rows.append(
                        {"measured_at": ts, "value": r.pulse, "metric": "Pulse"}
                    )

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
            ax.axhline(
                y=systolic_top, color=reference_color(theme, "systolic"), linewidth=1
            )
        if show_diastolic:
            ax.axhline(
                y=diastolic_top, color=reference_color(theme, "diastolic"), linewidth=1
            )
        ax.set_title(title, fontsize=14, pad=12)
        ax.set_xlabel("Date")
        ax.set_ylabel("mmHg / BPM")

        apply_time_axis(ax, start, end)
        fig.autofmt_xdate()
        return to_svg(fig, title)
