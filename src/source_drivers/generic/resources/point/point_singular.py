from abc import abstractmethod

from src.source_drivers.generic.models.point import GenericPointModel
from src.source_drivers.generic.resources.point.point_singular_base import GenericPointSingularBase


class GenericPointSingular(GenericPointSingularBase):
    @classmethod
    @abstractmethod
    def get_point(cls, **kwargs) -> GenericPointModel:
        return GenericPointModel.find_by_uuid(kwargs.get('uuid'))
