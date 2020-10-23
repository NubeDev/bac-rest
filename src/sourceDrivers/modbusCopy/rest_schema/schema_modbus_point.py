from src.rest_schema.schema_point import *
from copy import deepcopy

modbus_point_all_attributes = deepcopy(point_all_attributes)
modbus_point_all_attributes['mod_point_reg'] = {
    'type': int,
    'required': True,
    'help': '',
}
modbus_point_all_attributes['mod_point_reg_length'] = {
    'type': int,
    'required': True,
    'help': '',
}
modbus_point_all_attributes['mod_point_type'] = {
    'type': str,
    'required': True,
    'help': '',
}
modbus_point_all_attributes['mod_point_data_type'] = {
    'type': str,
    'required': True,
    'help': '',
}
modbus_point_all_attributes['mod_point_data_endian'] = {
    'type': str,
    'required': True,
    'help': '',
}
modbus_point_all_attributes['mod_point_data_offset'] = {
    'type': int,
    'required': True,
    'help': '',
}
modbus_point_all_attributes['mod_point_data_round'] = {
    'type': int,
    'required': True,
    'help': '',
}
modbus_point_all_attributes['mod_point_timeout'] = {
    'type': int,
    'required': True,
    'help': '',
}
modbus_point_all_attributes['mod_point_timeout_global'] = {
    'type': bool,
    'required': True,
    'help': '',
}