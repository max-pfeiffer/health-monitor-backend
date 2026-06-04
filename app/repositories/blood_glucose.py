from typing import Optional

from sqlmodel import Session, select

from app.models.blood_glucose import BloodGlucose
from app.schemas.blood_glucose import BloodGlucoseCreate, BloodGlucoseUpdate


class BloodGlucoseRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: BloodGlucoseCreate) -> BloodGlucose:
        record = BloodGlucose(**data.model_dump())
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get(self, record_id: int) -> Optional[BloodGlucose]:
        return self.session.get(BloodGlucose, record_id)

    def get_all(self) -> list[BloodGlucose]:
        return list(self.session.exec(select(BloodGlucose)).all())

    def update(self, record_id: int, data: BloodGlucoseUpdate) -> Optional[BloodGlucose]:
        record = self.session.get(BloodGlucose, record_id)
        if not record:
            return None
        record.sqlmodel_update(data.model_dump(exclude_unset=True))
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def delete(self, record_id: int) -> bool:
        record = self.session.get(BloodGlucose, record_id)
        if not record:
            return False
        self.session.delete(record)
        self.session.commit()
        return True
