from flask_restful import abort, marshal_with, reqparse

from src.source_drivers.modbus.models.point import ModbusPointModel
from src.source_drivers.modbus.resources.point.point_base import ModbusPointBase
from src.source_drivers.modbus.resources.rest_schema.schema_modbus_point import modbus_point_all_fields, \
    modbus_point_all_attributes


class ModbusPointSingular(ModbusPointBase):
    """
    It returns point with point_store object value, which has the current values of point_store for that particular
    point with last not null value and value_array
    """

    patch_parser = reqparse.RequestParser()
    for attr in modbus_point_all_attributes:
        patch_parser.add_argument(attr,
                                  type=modbus_point_all_attributes[attr]['type'],
                                  required=False,
                                  store_missing=False)

    @classmethod
    @marshal_with(modbus_point_all_fields)
    def get(cls, uuid):
        point = ModbusPointModel.find_by_uuid(uuid)
        if not point:
            abort(404, message=f'Modbus Point not found')
        return point

    @classmethod
    @marshal_with(modbus_point_all_fields)
    def put(cls, uuid):
        data = ModbusPointSingular.parser.parse_args()
        point = ModbusPointModel.find_by_uuid(uuid)
        if point is None:
            return cls.add_point(data, uuid)
        else:
            try:
                # cls.validate_modbus_point_json(data)
                point.update(**data)
                return ModbusPointModel.find_by_uuid(uuid)
            except Exception as e:
                abort(500, message=str(e))

    @classmethod
    @marshal_with(modbus_point_all_fields)
    def patch(cls, uuid):
        data = ModbusPointSingular.patch_parser.parse_args()
        point = ModbusPointModel.find_by_uuid(uuid)
        if point is None:
            abort(404, message=f'Modbus Point not found')
        else:
            try:
                # cls.validate_modbus_point_json(data)
                point.update(**data)
                return ModbusPointModel.find_by_uuid(uuid)
            except Exception as e:
                abort(500, message=str(e))

    @classmethod
    def delete(cls, uuid):
        point = ModbusPointModel.find_by_uuid(uuid)
        if point:
            point.delete_from_db()
        return '', 204

# from flask_restful import Resource
# from src.event_dispatcher import EventDispatcher
# from src.services.event_service_base import Event, EventCallableBlocking, EventType
# from src.source_drivers.modbus.services.rtu_polling import RtuPolling
#
#
# class TestEndPoint(Resource):
#
#     @classmethod
#     def get(cls, thing):
#         event = EventCallableBlocking(RtuPolling.temporary_test_func, (thing, thing))
#         EventDispatcher.dispatch_to_source_only(
#             event, 'modbus_rtu')
#         event.condition.wait()
#         if event.error:
#             abort(500, message='unknown error')
#         else:
#             return event.data, 200
