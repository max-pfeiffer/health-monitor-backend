import json
from datetime import datetime
from typing import Literal, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from pydantic import TypeAdapter, ValidationError
from sqlmodel import Session

from app.auth import get_current_user_id
from app.database import get_session
from app.diagrams.ketones import render_chart
from app.repositories.exceptions import DuplicateMeasurementError
from app.repositories.ketones import KetonesRepository
from app.routers.chart_response import (
    CHART_RESPONSES,
    SVGChartResponse,
    chart_response,
    validate_time_range,
)
from app.schemas.ketones import KetonesCreate, KetonesRead, KetonesUpdate

router = APIRouter(prefix="/ketones", tags=["ketones"])


@router.get("/", response_model=list[KetonesRead])
def list_ketones(
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    return KetonesRepository(session).get_all(user_id)


@router.post("/", response_model=KetonesRead, status_code=201)
def create_ketones(
    data: KetonesCreate,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    try:
        return KetonesRepository(session).create(data, user_id)
    except DuplicateMeasurementError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/import", status_code=201)
async def import_ketones(
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
        items = TypeAdapter(list[KetonesCreate]).validate_python(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())
    try:
        KetonesRepository(session).bulk_create(items, user_id)
    except DuplicateMeasurementError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return Response(status_code=201)


@router.get("/chart", response_class=SVGChartResponse, responses=CHART_RESPONSES)
def ketones_chart(
    request: Request,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    theme: Literal["light", "dark"] = "light",
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    validate_time_range(start, end)
    records = KetonesRepository(session).get_in_range(user_id, start=start, end=end)
    return chart_response(
        request,
        records,
        lambda: render_chart(records, start=start, end=end, theme=theme),
        etag_parts=[start, end, theme],
    )


@router.get("/{record_id}", response_model=KetonesRead)
def get_ketones(
    record_id: int,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    record = KetonesRepository(session).get(record_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.put("/{record_id}", response_model=KetonesRead)
def update_ketones(
    record_id: int,
    data: KetonesUpdate,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    try:
        record = KetonesRepository(session).update(record_id, data, user_id)
    except DuplicateMeasurementError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.delete("/{record_id}", status_code=204)
def delete_ketones(
    record_id: int,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    if not KetonesRepository(session).delete(record_id, user_id):
        raise HTTPException(status_code=404, detail="Record not found")
