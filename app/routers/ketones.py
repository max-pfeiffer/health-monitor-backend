from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.database import get_session
from app.repositories.ketones import KetonesRepository
from app.schemas.ketones import KetonesCreate, KetonesRead, KetonesUpdate

router = APIRouter(prefix="/api/v1/ketones", tags=["ketones"])


@router.get("/", response_model=list[KetonesRead])
def list_ketones(session: Session = Depends(get_session)):
    return KetonesRepository(session).get_all()


@router.post("/", response_model=KetonesRead, status_code=201)
def create_ketones(data: KetonesCreate, session: Session = Depends(get_session)):
    return KetonesRepository(session).create(data)


@router.get("/{record_id}", response_model=KetonesRead)
def get_ketones(record_id: int, session: Session = Depends(get_session)):
    record = KetonesRepository(session).get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.put("/{record_id}", response_model=KetonesRead)
def update_ketones(record_id: int, data: KetonesUpdate, session: Session = Depends(get_session)):
    record = KetonesRepository(session).update(record_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.delete("/{record_id}", status_code=204)
def delete_ketones(record_id: int, session: Session = Depends(get_session)):
    if not KetonesRepository(session).delete(record_id):
        raise HTTPException(status_code=404, detail="Record not found")
