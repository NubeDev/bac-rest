from abc import abstractmethod

from flask_restful import marshal_with, reqparse
from rubix_http.exceptions.exception import NotFoundException

from src.drivers.generic.models.point import GenericPointModel
from src.drivers.generic.resources.point.point_base import GenericPointBase
from src.drivers.generic.resources.rest_schema.schema_generic_point import generic_point_all_fields, \
    generic_point_all_attributes
from src.services.points_registry import PointsRegistry


class GenericPointSingular(GenericPointBase):
    patch_parser = reqparse.RequestParser()
    for attr in generic_point_all_attributes:
        patch_parser.add_argument(attr,
                                  type=generic_point_all_attributes[attr]['type'],
                                  required=False,
                                  store_missing=False)

    @classmethod
    @marshal_with(generic_point_all_fields)
    def get(cls, **kwargs):
        point: GenericPointModel = cls.get_point(**kwargs)
        if not point:
            raise NotFoundException('Generic Point not found')
        return point

    @classmethod
    @marshal_with(generic_point_all_fields)
    def put(cls, **kwargs):
        data: dict = cls.parser.parse_args()
        point: GenericPointModel = cls.get_point(**kwargs)
        if point is None:
            return cls.add_point(data)
        return cls.update_point(data, point)

    @classmethod
    def update_point(cls, data: dict, point: GenericPointModel) -> GenericPointModel:
        updated_point: GenericPointModel = point.update(**data)
        PointsRegistry().update_point(updated_point)
        return updated_point

    @classmethod
    @marshal_with(generic_point_all_fields)
    def patch(cls, **kwargs):
        data: dict = cls.patch_parser.parse_args()
        point: GenericPointModel = cls.get_point(**kwargs)
        if point is None:
            raise NotFoundException('Generic Point not found')
        return cls.update_point(data, point)

    @classmethod
    def delete(cls, **kwargs):
        point: GenericPointModel = cls.get_point(**kwargs)
        if point is None:
            raise NotFoundException('Generic Point not found')
        point.delete_from_db()
        PointsRegistry().delete_point(point.uuid)
        return '', 204

    @classmethod
    @abstractmethod
    def get_point(cls, **kwargs) -> GenericPointModel:
        raise NotImplementedError


class GenericPointSingularByUUID(GenericPointSingular):
    @classmethod
    @abstractmethod
    def get_point(cls, **kwargs) -> GenericPointModel:
        return GenericPointModel.find_by_uuid(kwargs.get('uuid'))


class GenericPointSingularByName(GenericPointSingular):
    @classmethod
    @abstractmethod
    def get_point(cls, **kwargs) -> GenericPointModel:
        return GenericPointModel.find_by_name(kwargs.get('network_name'), kwargs.get('device_name'),
                                              kwargs.get('point_name'))
