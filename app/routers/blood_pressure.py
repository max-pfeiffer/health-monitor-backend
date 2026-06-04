from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.database import get_session
from app.repositories.blood_pressure import BloodPressureRepository
from app.schemas.blood_pressure import BloodPressureCreate, BloodPressureRead, BloodPressureUpdate

router = APIRouter(prefix="/api/v1/blood-pressure", tags=["blood-pressure"])


@router.get("/", response_model=list[BloodPressureRead])
def list_blood_pressure(session: Session = Depends(get_session)):
    return BloodPressureRepository(session).get_all()


@router.post("/", response_model=BloodPressureRead, status_code=201)
def create_blood_pressure(data: BloodPressureCreate, session: Session = Depends(get_session)):
    return BloodPressureRepository(session).create(data)


@router.get("/{record_id}", response_model=BloodPressureRead)
def get_blood_pressure(record_id: int, session: Session = Depends(get_session)):
    record = BloodPressureRepository(session).get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.put("/{record_id}", response_model=BloodPressureRead)
def update_blood_pressure(record_id: int, data: BloodPressureUpdate, session: Session = Depends(get_session)):
    record = BloodPressureRepository(session).update(record_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.delete("/{record_id}", status_code=204)
def delete_blood_pressure(record_id: int, session: Session = Depends(get_session)):
    if not BloodPressureRepository(session).delete(record_id):
        raise HTTPException(status_code=404, detail="Record not found")
