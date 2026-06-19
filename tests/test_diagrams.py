import re
from datetime import datetime
from decimal import Decimal
from io import BytesIO

import pytest

from app.diagrams import blood_glucose, blood_pressure, ketones
from app.models.blood_glucose import BloodGlucose
from app.models.blood_pressure import BloodPressure
from app.models.ketones import Ketones


def _make_blood_pressure(**kwargs) -> BloodPressure:
    defaults = dict(
        systolic=120, diastolic=80, measured_at=datetime(2024, 1, 15, 10, 0)
    )
    return BloodPressure(**{**defaults, **kwargs})


def _make_blood_glucose(**kwargs) -> BloodGlucose:
    defaults = dict(value=Decimal("5.60"), measured_at=datetime(2024, 1, 15, 10, 0))
    return BloodGlucose(**{**defaults, **kwargs})


def _make_ketones(**kwargs) -> Ketones:
    defaults = dict(value=Decimal("0.50"), measured_at=datetime(2024, 1, 15, 10, 0))
    return Ketones(**{**defaults, **kwargs})


def _is_svg(buf: BytesIO) -> bool:
    return b"<svg" in buf.read()


def _svg_root_tag(buf: BytesIO) -> str:
    text = buf.read().decode("utf-8")
    match = re.search(r"<svg\b[^>]*>", text)
    assert match is not None
    return match.group(0)


def _all_renderers():
    return [
        lambda theme="light": blood_pressure.render_chart(
            [_make_blood_pressure()], None, None, 135, 85, True, True, True, theme
        ),
        lambda theme="light": blood_glucose.render_chart(
            [_make_blood_glucose()], None, None, theme
        ),
        lambda theme="light": ketones.render_chart(
            [_make_ketones()], None, None, theme
        ),
    ]


# --- Responsive / accessible SVG (shared behaviour) ---


@pytest.mark.parametrize("render", _all_renderers())
def test_chart_is_responsive(render):
    root = _svg_root_tag(render())
    # viewBox is preserved so the SVG keeps its aspect ratio when scaled.
    assert "viewBox=" in root
    # Fixed pt width/height are stripped so it scales to its container via CSS.
    assert "width=" not in root
    assert "height=" not in root


@pytest.mark.parametrize("render", _all_renderers())
def test_chart_has_accessibility_markup(render):
    buf = render()
    root = _svg_root_tag(buf)
    assert 'role="img"' in root
    buf.seek(0)
    assert b"<title>" in buf.read()


@pytest.mark.parametrize("render", _all_renderers())
def test_chart_dark_theme_renders(render):
    assert _is_svg(render("dark"))


# --- Blood Pressure ---


def test_blood_pressure_chart_empty():
    buf = blood_pressure.render_chart([], None, None, 135, 85, True, True, True)
    assert isinstance(buf, BytesIO)
    assert _is_svg(buf)


def test_blood_pressure_chart_with_data():
    records = [
        _make_blood_pressure(systolic=120, diastolic=80, pulse=72),
        _make_blood_pressure(
            systolic=130, diastolic=85, measured_at=datetime(2024, 2, 1, 8, 0)
        ),
    ]
    buf = blood_pressure.render_chart(records, None, None, 135, 85, True, True, True)
    assert _is_svg(buf)


def test_blood_pressure_chart_with_time_range():
    records = [_make_blood_pressure()]
    buf = blood_pressure.render_chart(
        records,
        datetime(2024, 1, 1),
        datetime(2024, 12, 31),
        135,
        85,
        True,
        True,
        True,
    )
    assert _is_svg(buf)


def test_blood_pressure_chart_hide_systolic():
    records = [_make_blood_pressure()]
    buf = blood_pressure.render_chart(records, None, None, 135, 85, False, True, True)
    assert _is_svg(buf)


def test_blood_pressure_chart_hide_diastolic():
    records = [_make_blood_pressure()]
    buf = blood_pressure.render_chart(records, None, None, 135, 85, True, False, True)
    assert _is_svg(buf)


def test_blood_pressure_chart_hide_pulse():
    records = [_make_blood_pressure(pulse=72)]
    buf = blood_pressure.render_chart(records, None, None, 135, 85, True, True, False)
    assert _is_svg(buf)


def test_blood_pressure_chart_no_metrics_shown():
    records = [_make_blood_pressure()]
    buf = blood_pressure.render_chart(records, None, None, 135, 85, False, False, False)
    assert _is_svg(buf)


# --- Blood Glucose ---


def test_blood_glucose_chart_empty():
    buf = blood_glucose.render_chart([], None, None)
    assert isinstance(buf, BytesIO)
    assert _is_svg(buf)


def test_blood_glucose_chart_with_data():
    records = [
        _make_blood_glucose(value=Decimal("5.60")),
        _make_blood_glucose(
            value=Decimal("7.20"), measured_at=datetime(2024, 2, 1, 8, 0)
        ),
    ]
    buf = blood_glucose.render_chart(records, None, None)
    assert _is_svg(buf)


def test_blood_glucose_chart_with_time_range():
    records = [_make_blood_glucose()]
    buf = blood_glucose.render_chart(
        records, datetime(2024, 1, 1), datetime(2024, 12, 31)
    )
    assert _is_svg(buf)


def test_blood_glucose_chart_start_only():
    records = [_make_blood_glucose()]
    buf = blood_glucose.render_chart(records, datetime(2024, 1, 1), None)
    assert _is_svg(buf)


def test_blood_glucose_chart_end_only():
    records = [_make_blood_glucose()]
    buf = blood_glucose.render_chart(records, None, datetime(2024, 12, 31))
    assert _is_svg(buf)


# --- Ketones ---


def test_ketones_chart_empty():
    buf = ketones.render_chart([], None, None)
    assert isinstance(buf, BytesIO)
    assert _is_svg(buf)


def test_ketones_chart_with_data():
    records = [
        _make_ketones(value=Decimal("0.50")),
        _make_ketones(value=Decimal("1.20"), measured_at=datetime(2024, 2, 1, 8, 0)),
    ]
    buf = ketones.render_chart(records, None, None)
    assert _is_svg(buf)


def test_ketones_chart_with_time_range():
    records = [_make_ketones()]
    buf = ketones.render_chart(records, datetime(2024, 1, 1), datetime(2024, 12, 31))
    assert _is_svg(buf)


def test_ketones_chart_start_only():
    records = [_make_ketones()]
    buf = ketones.render_chart(records, datetime(2024, 1, 1), None)
    assert _is_svg(buf)


def test_ketones_chart_end_only():
    records = [_make_ketones()]
    buf = ketones.render_chart(records, None, datetime(2024, 12, 31))
    assert _is_svg(buf)
