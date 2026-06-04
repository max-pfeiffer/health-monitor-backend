from datetime import datetime
from typing import Optional

from sqlmodel import Session, col, select

from app.models.ketones import Ketones
from app.schemas.ketones import KetonesCreate, KetonesUpdate


class KetonesRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: KetonesCreate) -> Ketones:
        record = Ketones(**data.model_dump())
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get(self, record_id: int) -> Optional[Ketones]:
        return self.session.get(Ketones, record_id)

    def get_all(self) -> list[Ketones]:
        return list(self.session.exec(select(Ketones)).all())

    def get_in_range(
        self, start: Optional[datetime] = None, end: Optional[datetime] = None
    ) -> list[Ketones]:
        query = select(Ketones).order_by(Ketones.measured_at)
        if start is not None:
            query = query.where(Ketones.measured_at >= start)
        if end is not None:
            query = query.where(Ketones.measured_at <= end)
        return list(self.session.exec(query).all())

    def bulk_create(self, items: list[KetonesCreate]) -> list[Ketones]:
        records = [Ketones(**item.model_dump()) for item in items]
        self.session.add_all(records)
        self.session.flush()
        ids = [record.id for record in records]
        self.session.commit()
        return list(
            self.session.exec(
                select(Ketones).where(col(Ketones.id).in_(ids))
            ).all()
        )

    def update(self, record_id: int, data: KetonesUpdate) -> Optional[Ketones]:
        record = self.session.get(Ketones, record_id)
        if not record:
            return None
        record.sqlmodel_update(data.model_dump(exclude_unset=True))
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def delete(self, record_id: int) -> bool:
        record = self.session.get(Ketones, record_id)
        if not record:
            return False
        self.session.delete(record)
        self.session.commit()
        return True
