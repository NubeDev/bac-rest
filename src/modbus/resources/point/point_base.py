from flask_restful import Resource, reqparse, abort

from src.modbus.models.device import ModbusDeviceModel
from src.modbus.models.point import ModbusPointModel


class ModbusPointBase(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('name', type=str, required=True)
    parser.add_argument('reg', type=int, required=True)
    parser.add_argument('reg_length', type=int, required=True)
    parser.add_argument('type', type=str, required=True)
    parser.add_argument('enable', type=bool, required=True)
    parser.add_argument('write_value', type=int, required=True)
    parser.add_argument('data_type', type=str, required=True)
    parser.add_argument('data_endian', type=str, required=True)
    parser.add_argument('data_round', type=int, required=True)
    parser.add_argument('data_offset', type=str, required=True)
    parser.add_argument('timeout', type=int, required=True)
    parser.add_argument('timeout_global', type=bool, required=True)
    parser.add_argument('prevent_duplicates', type=bool, required=True)
    parser.add_argument('prevent_duplicates_global', type=bool, required=True)
    parser.add_argument('write_ok', type=bool, required=False)
    parser.add_argument('fault', type=bool, required=False)
    parser.add_argument('last_poll_timestamp', type=str, required=False)
    parser.add_argument('fault_timestamp', type=str, required=False)
    parser.add_argument('value', type=int, required=False)
    parser.add_argument('value_array', type=str, required=False)
    parser.add_argument('device_uuid', type=str, required=True)

    @staticmethod
    def create_point_model_obj(uuid, data):
        return ModbusPointModel(uuid=uuid, **data)

    def add_point(self, data, uuid):
        self.abort_if_device_does_not_exist(data.device_uuid)
        try:
            point = ModbusPointBase.create_point_model_obj(uuid, data)
            point.save_to_db()
            return point
        except Exception as e:
            abort(500, message=str(e))

    def abort_if_device_does_not_exist(self, device_uuid):
        if not ModbusDeviceModel.find_by_uuid(device_uuid):
            abort(400, message='Network does not exist of that device_uuid')
