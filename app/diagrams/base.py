"""Shared helpers for rendering health metric charts as responsive SVGs."""

import re
from datetime import datetime
from io import BytesIO
from typing import Literal, Optional
from xml.sax.saxutils import escape

import matplotlib.dates as mdates
import pandas as pd
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.figure import Figure

Theme = Literal["light", "dark"]

# rcParams applied per request on top of the global "ticks" style. Light keeps
# matplotlib defaults; dark switches text/axis colors so the chart stays legible
# on a dark page (the background itself is left transparent).
_THEME_RC: dict[Theme, dict[str, str]] = {
    "light": {},
    "dark": {
        "text.color": "#e0e0e0",
        "axes.labelcolor": "#e0e0e0",
        "axes.titlecolor": "#e0e0e0",
        "axes.edgecolor": "#9e9e9e",
        "xtick.color": "#e0e0e0",
        "ytick.color": "#e0e0e0",
        "xtick.labelcolor": "#e0e0e0",
        "ytick.labelcolor": "#e0e0e0",
    },
}

# Reference-line colors per theme (e.g. blood pressure systolic/diastolic caps).
_REFERENCE_COLORS: dict[Theme, dict[str, str]] = {
    "light": {"systolic": "red", "diastolic": "purple"},
    "dark": {"systolic": "#ff6b6b", "diastolic": "#c792ea"},
}

# Matches the opening <svg ...> root tag so we can post-process it.
_SVG_OPEN_TAG_RE = re.compile(r"<svg\b[^>]*>")
# Matches width="..." / height="..." attributes to strip from the root tag.
_SVG_SIZE_ATTR_RE = re.compile(r'\s+(?:width|height)="[^"]*"')


def configure_global_style() -> None:
    """Apply process-wide seaborn/matplotlib defaults once at app startup.

    This replaces calling ``sns.set_theme`` on every request, which mutated
    global rcParams from the request threadpool.
    """
    sns.set_theme(style="ticks")


def _style(theme: Theme):
    """Context manager scoping request-specific styling to a single render."""
    return sns.axes_style("ticks", rc=_THEME_RC.get(theme, {}))


def reference_color(theme: Theme, name: str) -> str:
    """Return the themed color for a named reference line."""
    return _REFERENCE_COLORS.get(theme, _REFERENCE_COLORS["light"])[name]


def apply_time_axis(
    ax: Axes, start: Optional[datetime], end: Optional[datetime]
) -> None:
    """Format the x-axis as dates and constrain it to the requested range."""
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    if start is not None or end is not None:
        xlim = list(ax.get_xlim())
        if start is not None:
            xlim[0] = mdates.date2num(start)
        if end is not None:
            xlim[1] = mdates.date2num(end)
        ax.set_xlim(xlim)


def _make_responsive(svg: bytes, title: str) -> bytes:
    """Strip the fixed pt size from the <svg> root and add accessibility markup.

    Removing the ``width``/``height`` attributes (while keeping ``viewBox``) lets
    the SVG scale to its container via CSS. A ``role="img"`` and a ``<title>``
    child are added so screen readers announce the chart.
    """
    text = svg.decode("utf-8")
    match = _SVG_OPEN_TAG_RE.search(text)
    if match is None:
        return svg

    open_tag = _SVG_SIZE_ATTR_RE.sub("", match.group(0))
    if "role=" not in open_tag:
        open_tag = open_tag[:-1] + ' role="img">'
    open_tag += f"<title>{escape(title)}</title>"

    return (text[: match.start()] + open_tag + text[match.end() :]).encode("utf-8")


def to_svg(fig: Figure, title: str) -> BytesIO:
    """Render the figure to a transparent, responsive, titled SVG buffer."""
    raw = BytesIO()
    fig.savefig(raw, format="svg", bbox_inches="tight", transparent=True)
    return BytesIO(_make_responsive(raw.getvalue(), title))


def render_single_series(
    records: list,
    *,
    title: str,
    ylabel: str,
    theme: Theme = "light",
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> BytesIO:
    """Render a single-value time series (shared by glucose and ketones)."""
    with _style(theme):
        fig = Figure(figsize=(10, 4))
        ax = fig.add_subplot(1, 1, 1)

        if records:
            df = pd.DataFrame(
                {"measured_at": r.measured_at, "value": float(r.value)} for r in records
            )
            sns.lineplot(data=df, x="measured_at", y="value", marker="o", ax=ax)

        ax.set_title(title, fontsize=14, pad=12)
        ax.set_xlabel("Date")
        ax.set_ylabel(ylabel)

        apply_time_axis(ax, start, end)
        fig.autofmt_xdate()
        return to_svg(fig, title)
