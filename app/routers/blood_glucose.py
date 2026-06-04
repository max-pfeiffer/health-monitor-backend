from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.database import get_session
from app.repositories.blood_glucose import BloodGlucoseRepository
from app.schemas.blood_glucose import BloodGlucoseCreate, BloodGlucoseRead, BloodGlucoseUpdate

router = APIRouter(prefix="/api/v1/blood-glucose", tags=["blood-glucose"])


@router.get("/", response_model=list[BloodGlucoseRead])
def list_blood_glucose(session: Session = Depends(get_session)):
    return BloodGlucoseRepository(session).get_all()


@router.post("/", response_model=BloodGlucoseRead, status_code=201)
def create_blood_glucose(data: BloodGlucoseCreate, session: Session = Depends(get_session)):
    return BloodGlucoseRepository(session).create(data)


@router.get("/{record_id}", response_model=BloodGlucoseRead)
def get_blood_glucose(record_id: int, session: Session = Depends(get_session)):
    record = BloodGlucoseRepository(session).get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.put("/{record_id}", response_model=BloodGlucoseRead)
def update_blood_glucose(record_id: int, data: BloodGlucoseUpdate, session: Session = Depends(get_session)):
    record = BloodGlucoseRepository(session).update(record_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.delete("/{record_id}", status_code=204)
def delete_blood_glucose(record_id: int, session: Session = Depends(get_session)):
    if not BloodGlucoseRepository(session).delete(record_id):
        raise HTTPException(status_code=404, detail="Record not found")
