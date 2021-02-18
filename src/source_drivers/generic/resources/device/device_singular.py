from src.source_drivers.generic.models.device import GenericDeviceModel
from src.source_drivers.generic.resources.device.device_singular_base import GenericDeviceSingularBase


class GenericDeviceSingular(GenericDeviceSingularBase):
    @classmethod
    def get_device(cls, **kwargs) -> GenericDeviceModel:
        return GenericDeviceModel.find_by_uuid(kwargs.get('uuid'))
