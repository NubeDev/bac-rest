import uuid
from flask_restful import marshal_with

from src.source_drivers.modbus.models.network import ModbusNetworkModel
from src.source_drivers.modbus.resources.mod_fields import network_fields
from src.source_drivers.modbus.resources.network.network_base import ModbusNetworkBase


class ModbusNetworkPlural(ModbusNetworkBase):
    @marshal_with(network_fields, envelope="networks")
    def get(self):
        return ModbusNetworkModel.query.all()

    @marshal_with(network_fields)
    def post(self):
        _uuid = str(uuid.uuid4())
        data = ModbusNetworkPlural.parser.parse_args()
        return self.add_network(_uuid, data)