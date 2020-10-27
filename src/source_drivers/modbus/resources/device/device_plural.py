import uuid
from flask_restful import marshal_with

from src.source_drivers.modbus.models.device import ModbusDeviceModel
from src.source_drivers.modbus.resources.device.device_base import ModbusDeviceBase
from src.source_drivers.modbus.resources.mod_fields import device_fields


class ModbusDevicePlural(ModbusDeviceBase):
    @marshal_with(device_fields, envelope="devices")
    def get(self):
        return ModbusDeviceModel.query.all()

    @marshal_with(device_fields)
    def post(self):
        _uuid = str(uuid.uuid4())
        data = ModbusDevicePlural.parser.parse_args()
        return self.add_device(_uuid, data)