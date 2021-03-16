import json
import re

from sqlalchemy.orm import validates

from src import db
from src.enums.model import ModelEvent
from src.event_dispatcher import EventDispatcher
from src.models.model_base import ModelBase
from src.services.event_service_base import EventType, Event


class ScheduleModel(ModelBase):
    __tablename__ = 'schedules'
    uuid = db.Column(db.String(80), primary_key=True, nullable=False)
    name = db.Column(db.String(80), nullable=False, unique=True)

    @validates('name')
    def validate_name(self, _, value):
        if not re.match("^([A-Za-z0-9_-])+$", value):
            raise ValueError("name should be alphanumeric and can contain '_', '-'")
        return value

    def __repr__(self):
        return f"Schedule(uuid = {self.uuid})"

    def get_model_event(self) -> ModelEvent:
        return ModelEvent.SCHEDULE

    def get_model_event_type(self) -> EventType:
        return EventType.SCHEDULE_MODEL

    def update(self, **kwargs):
        if super().update(**kwargs):
            self.publish_schedules()
        return self

    def delete_from_db(self):
        super().delete_from_db()
        self.publish_schedules()

    def save_to_db(self):
        super().save_to_db()
        self.publish_schedules()

    def publish_schedules(self):
        # TODO: better use of dispatching
        schedules = self.find_all()
        payload = [{'uuid': s.uuid, 'name': s.name} for s in schedules]
        event = Event(EventType.SCHEDULES, json.dumps(payload))
        EventDispatcher().dispatch_from_service(None, event, None)
