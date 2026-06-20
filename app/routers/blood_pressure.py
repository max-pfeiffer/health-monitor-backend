import json
from datetime import datetime
from typing import Literal, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from pydantic import TypeAdapter, ValidationError
from sqlmodel import Session

from app.auth import get_current_user_id
from app.database import get_session
from app.diagrams.blood_pressure import render_chart
from app.repositories.blood_pressure import BloodPressureRepository
from app.repositories.exceptions import DuplicateMeasurementError
from app.routers.chart_response import (
    CHART_RESPONSES,
    SVGChartResponse,
    chart_response,
    validate_time_range,
)
from app.schemas.blood_pressure import (
    BloodPressureCreate,
    BloodPressureRead,
    BloodPressureUpdate,
)

router = APIRouter(prefix="/blood-pressure", tags=["blood-pressure"])


@router.get("/", response_model=list[BloodPressureRead])
def list_blood_pressure(
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    return BloodPressureRepository(session).get_all(user_id)


@router.post("/", response_model=BloodPressureRead, status_code=201)
def create_blood_pressure(
    data: BloodPressureCreate,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    try:
        return BloodPressureRepository(session).create(data, user_id)
    except DuplicateMeasurementError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/import", status_code=201)
async def import_blood_pressure(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    content = await file.read()
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid JSON: {exc}")
    try:
        items = TypeAdapter(list[BloodPressureCreate]).validate_python(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())
    try:
        BloodPressureRepository(session).bulk_create(items, user_id)
    except DuplicateMeasurementError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return Response(status_code=201)


@router.get("/chart", response_class=SVGChartResponse, responses=CHART_RESPONSES)
def blood_pressure_chart(
    request: Request,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    systolic_top: int = Query(135, ge=0, le=400),
    diastolic_top: int = Query(85, ge=0, le=400),
    show_systolic: bool = True,
    show_diastolic: bool = True,
    show_pulse: bool = True,
    theme: Literal["light", "dark"] = "light",
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    validate_time_range(start, end)
    records = BloodPressureRepository(session).get_in_range(
        user_id, start=start, end=end
    )
    return chart_response(
        request,
        records,
        lambda: render_chart(
            records,
            start=start,
            end=end,
            systolic_top=systolic_top,
            diastolic_top=diastolic_top,
            show_systolic=show_systolic,
            show_diastolic=show_diastolic,
            show_pulse=show_pulse,
            theme=theme,
        ),
        etag_parts=[
            start,
            end,
            systolic_top,
            diastolic_top,
            show_systolic,
            show_diastolic,
            show_pulse,
            theme,
        ],
    )


@router.get("/{record_id}", response_model=BloodPressureRead)
def get_blood_pressure(
    record_id: int,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    record = BloodPressureRepository(session).get(record_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.put("/{record_id}", response_model=BloodPressureRead)
def update_blood_pressure(
    record_id: int,
    data: BloodPressureUpdate,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    try:
        record = BloodPressureRepository(session).update(record_id, data, user_id)
    except DuplicateMeasurementError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.delete("/{record_id}", status_code=204)
def delete_blood_pressure(
    record_id: int,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    if not BloodPressureRepository(session).delete(record_id, user_id):
        raise HTTPException(status_code=404, detail="Record not found")
