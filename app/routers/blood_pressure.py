from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.database import get_session
from app.diagrams.blood_pressure import render_chart
from app.repositories.blood_pressure import BloodPressureRepository
from app.schemas.blood_pressure import (
    BloodPressureCreate,
    BloodPressureRead,
    BloodPressureUpdate,
)

router = APIRouter(prefix="/blood-pressure", tags=["blood-pressure"])


@router.get("/", response_model=list[BloodPressureRead])
def list_blood_pressure(session: Session = Depends(get_session)):
    return BloodPressureRepository(session).get_all()


@router.post("/", response_model=BloodPressureRead, status_code=201)
def create_blood_pressure(
    data: BloodPressureCreate, session: Session = Depends(get_session)
):
    return BloodPressureRepository(session).create(data)


@router.post("/import", response_model=list[BloodPressureRead], status_code=201)
def import_blood_pressure(
    data: list[BloodPressureCreate], session: Session = Depends(get_session)
):
    return BloodPressureRepository(session).bulk_create(data)


@router.get("/chart", response_class=StreamingResponse)
def blood_pressure_chart(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    session: Session = Depends(get_session),
):
    records = BloodPressureRepository(session).get_in_range(start=start, end=end)
    return StreamingResponse(
        render_chart(records, start=start, end=end), media_type="image/svg+xml"
    )


@router.get("/{record_id}", response_model=BloodPressureRead)
def get_blood_pressure(record_id: int, session: Session = Depends(get_session)):
    record = BloodPressureRepository(session).get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.put("/{record_id}", response_model=BloodPressureRead)
def update_blood_pressure(
    record_id: int, data: BloodPressureUpdate, session: Session = Depends(get_session)
):
    record = BloodPressureRepository(session).update(record_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.delete("/{record_id}", status_code=204)
def delete_blood_pressure(record_id: int, session: Session = Depends(get_session)):
    if not BloodPressureRepository(session).delete(record_id):
        raise HTTPException(status_code=404, detail="Record not found")
