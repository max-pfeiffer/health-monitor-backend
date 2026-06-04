from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.models.blood_pressure import BloodPressure
from app.schemas.blood_pressure import BloodPressureCreate, BloodPressureUpdate


class BloodPressureRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: BloodPressureCreate) -> BloodPressure:
        record = BloodPressure(**data.model_dump())
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get(self, record_id: int) -> Optional[BloodPressure]:
        return self.session.get(BloodPressure, record_id)

    def get_all(self) -> list[BloodPressure]:
        return list(self.session.exec(select(BloodPressure)).all())

    def get_in_range(
        self, start: Optional[datetime] = None, end: Optional[datetime] = None
    ) -> list[BloodPressure]:
        query = select(BloodPressure).order_by(BloodPressure.measured_at)
        if start is not None:
            query = query.where(BloodPressure.measured_at >= start)
        if end is not None:
            query = query.where(BloodPressure.measured_at <= end)
        return list(self.session.exec(query).all())

    def update(self, record_id: int, data: BloodPressureUpdate) -> Optional[BloodPressure]:
        record = self.session.get(BloodPressure, record_id)
        if not record:
            return None
        record.sqlmodel_update(data.model_dump(exclude_unset=True))
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def delete(self, record_id: int) -> bool:
        record = self.session.get(BloodPressure, record_id)
        if not record:
            return False
        self.session.delete(record)
        self.session.commit()
        return True
