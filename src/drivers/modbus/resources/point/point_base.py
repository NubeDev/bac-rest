import uuid

from flask_restful import reqparse
from rubix_http.resource import RubixResource

from src.drivers.modbus.models.point import ModbusPointModel
from src.drivers.modbus.resources.rest_schema.schema_modbus_point import modbus_point_all_attributes, \
    add_nested_priority_array_write
from src.models.point.priority_array import PriorityArrayModel


class ModbusPointBase(RubixResource):
    parser = reqparse.RequestParser()
    for attr in modbus_point_all_attributes:
        parser.add_argument(attr,
                            type=modbus_point_all_attributes[attr]['type'],
                            required=modbus_point_all_attributes[attr].get('required', False),
                            help=modbus_point_all_attributes[attr].get('help', None),
                            store_missing=False)
    add_nested_priority_array_write()

    @classmethod
    def add_point(cls, data):
        _uuid = str(uuid.uuid4())
        priority_array_write: dict = data.pop('priority_array_write', {})
        point = ModbusPointModel(
            uuid=_uuid,
            priority_array_write=PriorityArrayModel.create_priority_array_model(_uuid, priority_array_write),
            **data
        )
        point.save_to_db()
        return point
