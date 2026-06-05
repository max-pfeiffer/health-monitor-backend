import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import TypeAdapter, ValidationError
from sqlmodel import Session

from app.database import get_session
from app.diagrams.blood_glucose import render_chart
from app.repositories.blood_glucose import BloodGlucoseRepository
from app.repositories.exceptions import DuplicateMeasurementError
from app.schemas.blood_glucose import (
    BloodGlucoseCreate,
    BloodGlucoseRead,
    BloodGlucoseUpdate,
)

router = APIRouter(prefix="/blood-glucose", tags=["blood-glucose"])


@router.get("/", response_model=list[BloodGlucoseRead])
def list_blood_glucose(session: Session = Depends(get_session)):
    return BloodGlucoseRepository(session).get_all()


@router.post("/", response_model=BloodGlucoseRead, status_code=201)
def create_blood_glucose(
    data: BloodGlucoseCreate, session: Session = Depends(get_session)
):
    try:
        return BloodGlucoseRepository(session).create(data)
    except DuplicateMeasurementError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/import", status_code=201)
async def import_blood_glucose(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    content = await file.read()
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid JSON: {exc}")
    try:
        items = TypeAdapter(list[BloodGlucoseCreate]).validate_python(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())
    try:
        BloodGlucoseRepository(session).bulk_create(items)
    except DuplicateMeasurementError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return Response(status_code=201)


@router.get("/chart", response_class=StreamingResponse)
def blood_glucose_chart(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    session: Session = Depends(get_session),
):
    records = BloodGlucoseRepository(session).get_in_range(start=start, end=end)
    return StreamingResponse(
        render_chart(records, start=start, end=end), media_type="image/svg+xml"
    )


@router.get("/{record_id}", response_model=BloodGlucoseRead)
def get_blood_glucose(record_id: int, session: Session = Depends(get_session)):
    record = BloodGlucoseRepository(session).get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.put("/{record_id}", response_model=BloodGlucoseRead)
def update_blood_glucose(
    record_id: int, data: BloodGlucoseUpdate, session: Session = Depends(get_session)
):
    try:
        record = BloodGlucoseRepository(session).update(record_id, data)
    except DuplicateMeasurementError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.delete("/{record_id}", status_code=204)
def delete_blood_glucose(record_id: int, session: Session = Depends(get_session)):
    if not BloodGlucoseRepository(session).delete(record_id):
        raise HTTPException(status_code=404, detail="Record not found")
