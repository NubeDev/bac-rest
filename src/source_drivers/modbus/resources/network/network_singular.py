from flask_restful import marshal_with, abort

from src.source_drivers.modbus.interfaces.network.network import ModbusType, ModbusRtuParity
from src.source_drivers.modbus.models.network import ModbusNetworkModel
from src.source_drivers.modbus.resources.mod_fields import network_fields
from src.source_drivers.modbus.resources.network.network_plural import ModbusNetworkPlural
from src.source_drivers.modbus.resources.network.network_base import ModbusNetworkBase


class ModbusNetworkSingular(ModbusNetworkBase):

    @marshal_with(network_fields)
    def get(self, uuid):
        network = ModbusNetworkModel.find_by_uuid(uuid)
        if not network:
            abort(404, message='Modbus Network not found')
        return network

    @marshal_with(network_fields)
    def put(self, uuid):
        data = ModbusNetworkPlural.parser.parse_args()
        network = ModbusNetworkModel.find_by_uuid(uuid)
        if network is None:
            return self.add_network(uuid, data)
        else:
            try:
                if data.type:
                    data.type = ModbusType.__members__.get(data.type)
                if data.rtu_parity:
                    data.rtu_parity = ModbusRtuParity.__members__.get(data.rtu_parity)
                ModbusNetworkModel.filter_by_uuid(uuid).update(data)
                ModbusNetworkModel.commit()
                return ModbusNetworkModel.find_by_uuid(uuid)
            except Exception as e:
                abort(500, message=str(e))

    def delete(self, uuid):
        network = ModbusNetworkModel.find_by_uuid(uuid)
        if network:
            network.delete_from_db()
        return '', 204