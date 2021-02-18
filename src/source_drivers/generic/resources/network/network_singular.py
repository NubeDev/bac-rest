from src.source_drivers.generic.models.network import GenericNetworkModel
from src.source_drivers.generic.resources.network.network_singular_base import GenericNetworkSingularBase


class GenericNetworkSingular(GenericNetworkSingularBase):
    @classmethod
    def get_network(cls, **kwargs) -> GenericNetworkModel:
        return GenericNetworkModel.find_by_uuid(kwargs.get('uuid'))
