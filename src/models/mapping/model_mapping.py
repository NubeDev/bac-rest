from mrb.mapper import api_to_topic_mapper
from mrb.message import HttpMethod, Response
from mrb.validator import is_valid
from sqlalchemy.orm import validates

from src import db
from src.models.model_base import ModelBase
from src.services.event_service_base import EventType


class GBPointMapping(ModelBase):
    __tablename__ = 'generic_bacnet_points_mappings'

    generic_point_uuid = db.Column(db.String, db.ForeignKey('generic_points.uuid'), primary_key=True, nullable=False)
    bacnet_point_uuid = db.Column(db.String(80), nullable=False, unique=True)
    generic_point_name = db.Column(db.String(80), nullable=False)
    bacnet_point_name = db.Column(db.String(80), nullable=False)

    @validates('bacnet_point_uuid')
    def validate_bacnet_point_uuid(self, _, value):
        response: Response = api_to_topic_mapper(api=f'/api/bacnet/points/uuid/{value}',
                                                 destination_identifier=f'bacnet', http_method=HttpMethod.GET)
        if not is_valid(response):
            raise ValueError(response.message)
        return value

    @validates('generic_point_name')
    def validate_generic_point_name(self, _, value):
        if not value:
            raise ValueError('generic_point_name should not be null or blank')
        return value

    @validates('bacnet_point_name')
    def validate_bacnet_point_name(self, _, value):
        if not value:
            raise ValueError('bacnet_point_name should not be null or blank')
        return value

    def get_model_event_name(self) -> str:
        return 'generic_bacnet_points_mappings'

    def get_model_event_type(self) -> EventType:
        return EventType.MAPPING_UPDATE

    @classmethod
    def find_by_generic_point_uuid(cls, generic_point_uuid):
        return cls.query.filter_by(generic_point_uuid=generic_point_uuid).first()

    @classmethod
    def find_by_bacnet_point_uuid(cls, bacnet_point_uuid):
        return cls.query.filter_by(bacnet_point_uuid=bacnet_point_uuid).first()