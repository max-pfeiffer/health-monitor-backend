from datetime import datetime
from typing import Optional

from sqlmodel import Session, col, select

from app.models.blood_pressure import BloodPressure
from app.repositories.exceptions import DuplicateMeasurementError
from app.schemas.blood_pressure import BloodPressureCreate, BloodPressureUpdate


class BloodPressureRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: BloodPressureCreate) -> BloodPressure:
        if self._existing_measured_at({data.measured_at}):
            raise DuplicateMeasurementError(
                f"Measurement for {data.measured_at.isoformat()} already exists"
            )
        record = BloodPressure(**data.model_dump())
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def _existing_measured_at(self, timestamps: set[datetime]) -> set[datetime]:
        if not timestamps:
            return set()
        rows = self.session.exec(
            select(BloodPressure.measured_at).where(
                col(BloodPressure.measured_at).in_(timestamps)
            )
        ).all()
        return set(rows)

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

    def bulk_create(self, items: list[BloodPressureCreate]) -> list[BloodPressure]:
        timestamps = [item.measured_at for item in items]
        if len(set(timestamps)) != len(timestamps):
            raise DuplicateMeasurementError(
                "Payload contains multiple measurements with the same measured_at"
            )
        existing = self._existing_measured_at(set(timestamps))
        if existing:
            sample = sorted(ts.isoformat() for ts in existing)
            raise DuplicateMeasurementError(
                f"Measurements already exist for: {', '.join(sample)}"
            )
        records = [BloodPressure(**item.model_dump()) for item in items]
        self.session.add_all(records)
        self.session.flush()
        ids = [record.id for record in records]
        self.session.commit()
        return list(
            self.session.exec(
                select(BloodPressure).where(col(BloodPressure.id).in_(ids))
            ).all()
        )

    def update(
        self, record_id: int, data: BloodPressureUpdate
    ) -> Optional[BloodPressure]:
        record = self.session.get(BloodPressure, record_id)
        if not record:
            return None
        updates = data.model_dump(exclude_unset=True)
        new_measured_at = updates.get("measured_at")
        if new_measured_at is not None and new_measured_at != record.measured_at:
            conflict = self.session.exec(
                select(BloodPressure).where(
                    BloodPressure.measured_at == new_measured_at,
                    BloodPressure.id != record_id,
                )
            ).first()
            if conflict:
                raise DuplicateMeasurementError(
                    f"Measurement for {new_measured_at.isoformat()} already exists"
                )
        record.sqlmodel_update(updates)
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
