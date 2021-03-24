from flask import Blueprint
from flask_restful import Api

from src.drivers.generic.resources.device.device_plural import GenericDevicePlural
from src.drivers.generic.resources.device.device_singular import GenericDeviceSingularByUUID, \
    GenericDeviceSingularByName
from src.drivers.generic.resources.network.network_plural import GenericNetworkPlural
from src.drivers.generic.resources.network.network_singular import GenericNetworkSingularByUUID, \
    GenericNetworkSingularByName
from src.drivers.generic.resources.point.point_plural import GenericPointPlural
from src.drivers.generic.resources.point.point_singular import GenericPointSingularByUUID, \
    GenericPointSingularByName
from src.drivers.generic.resources.point.point_value_writer import GenericPointUUIDValueWriter, \
    GenericPointNameValueWriter
from src.drivers.modbus.resources.device.device_plural import ModbusDevicePlural
from src.drivers.modbus.resources.device.device_singular import ModbusDeviceSingularByUUID, \
    ModbusDeviceSingularByName
from src.drivers.modbus.resources.mapping.mapping import MPGBPMappingResourceList, \
    MPGBPMappingResourceByGenericPointUUID, MPGBPMappingResourceByBACnetPointUUID, \
    MPGBPMappingResourceByModbusPointUUID, MPGBPMappingResourceByUUID
from src.drivers.modbus.resources.network.network_plural import ModbusNetworkPlural
from src.drivers.modbus.resources.network.network_singular import ModbusNetworkSingularByName, \
    ModbusNetworkSingularByUUID
from src.drivers.modbus.resources.point.point_plural import ModbusPointPlural
from src.drivers.modbus.resources.point.point_poll import ModbusPointPollNonExisting, ModbusPointPoll
from src.drivers.modbus.resources.point.point_singular import ModbusPointSingularByUUID, \
    ModbusPointSingularByName
from src.drivers.modbus.resources.point.point_stores import ModbusPointPluralPointStore, ModbusPointStore, \
    ModbusDevicePointPluralPointStore
from src.drivers.modbus.resources.point.point_sync import MPToBPSync
from src.drivers.modbus.resources.point.point_value_writer import ModbusPointUUIDValueWriter, ModbusPointNameValueWriter
from src.resources.resource_device import DeviceResourceByUUID, DeviceResourceByName, DeviceResourceList
from src.resources.resource_network import NetworkResourceByUUID, NetworkResourceByName, NetworkResourceList
from src.resources.resource_point import PointResourceByUUID, PointResourceByName, PointResourceList
from src.resources.resource_schedule import ScheduleResourceByUUID, ScheduleResourceList
from src.resources.resource_setting import PostgresSettingResource, InfluxSettingResource
from src.system.resources.memory import GetSystemMem
from src.system.resources.ping import Ping

bp_network = Blueprint('networks', __name__, url_prefix='/api/networks')
api_network = Api(bp_network)
api_network.add_resource(NetworkResourceList, '')
api_network.add_resource(NetworkResourceByUUID, '/uuid/<string:uuid>')
api_network.add_resource(NetworkResourceByName, '/name/<string:name>')

bp_device = Blueprint('devices', __name__, url_prefix='/api/devices')
api_network = Api(bp_device)
api_network.add_resource(DeviceResourceList, '')
api_network.add_resource(DeviceResourceByUUID, '/uuid/<string:uuid>')
api_network.add_resource(DeviceResourceByName, '/name/<string:network_name>/<string:device_name>')

bp_point = Blueprint('points', __name__, url_prefix='/api/points')
api_point = Api(bp_point)
api_point.add_resource(PointResourceList, '')
api_point.add_resource(PointResourceByUUID, '/uuid/<string:uuid>')
api_point.add_resource(PointResourceByName, '/name/<string:network_name>/<string:device_name>/<string:point_name>')

bp_generic = Blueprint('generic', __name__, url_prefix='/api/generic')
api_generic = Api(bp_generic)
api_generic.add_resource(GenericNetworkPlural, '/networks')
api_generic.add_resource(GenericNetworkSingularByUUID, '/networks/uuid/<string:uuid>')
api_generic.add_resource(GenericNetworkSingularByName, '/networks/name/<string:name>')
api_generic.add_resource(GenericDevicePlural, '/devices')
api_generic.add_resource(GenericDeviceSingularByUUID, '/devices/uuid/<string:uuid>')
api_generic.add_resource(GenericDeviceSingularByName, '/devices/name/<string:network_name>/<string:device_name>')
api_generic.add_resource(GenericPointPlural, '/points')
api_generic.add_resource(GenericPointSingularByUUID, '/points/uuid/<string:uuid>')
api_generic.add_resource(GenericPointSingularByName,
                         '/points/name/<string:network_name>/<string:device_name>/<string:point_name>')
api_generic.add_resource(GenericPointUUIDValueWriter, '/points_value/uuid/<string:uuid>')
api_generic.add_resource(GenericPointNameValueWriter,
                         '/points_value/name/<string:network_name>/<string:device_name>/<string:point_name>')

bp_modbus = Blueprint('modbus', __name__, url_prefix='/api/modbus')
api_modbus = Api(bp_modbus)
api_modbus.add_resource(ModbusNetworkPlural, '/networks')
api_modbus.add_resource(ModbusNetworkSingularByUUID, '/networks/uuid/<string:uuid>')
api_modbus.add_resource(ModbusNetworkSingularByName, '/networks/name/<string:name>')
api_modbus.add_resource(ModbusDevicePlural, '/devices')
api_modbus.add_resource(ModbusDeviceSingularByUUID, '/devices/uuid/<string:uuid>')
api_modbus.add_resource(ModbusDeviceSingularByName, '/devices/name/<string:network_name>/<string:device_name>')
api_modbus.add_resource(ModbusPointPlural, '/points')
api_modbus.add_resource(ModbusPointSingularByUUID, '/points/uuid/<string:uuid>')
api_modbus.add_resource(ModbusPointSingularByName,
                        '/points/name/<string:network_name>/<string:device_name>/<string:point_name>')
api_modbus.add_resource(ModbusPointPoll, '/poll/point/<string:uuid>')
api_modbus.add_resource(ModbusPointPollNonExisting, '/poll/point')
api_modbus.add_resource(ModbusPointPluralPointStore, '/point_stores')
api_modbus.add_resource(ModbusPointStore, '/point_stores/<string:uuid>')
api_modbus.add_resource(ModbusDevicePointPluralPointStore, '/<string:device_uuid>/point_stores')
api_modbus.add_resource(ModbusPointUUIDValueWriter, '/points_value/uuid/<string:uuid>')
api_modbus.add_resource(ModbusPointNameValueWriter,
                        '/points_value/name/<string:network_name>/<string:device_name>/<string:point_name>')

# Modbus <> Generic|BACnet points mappings
bp_mapping_mp_gbp = Blueprint('mappings_mp_gbp', __name__, url_prefix='/api/mappings/mp_gbp')
api_mapping_mp_gbp = Api(bp_mapping_mp_gbp)
api_mapping_mp_gbp.add_resource(MPGBPMappingResourceList, '')
api_mapping_mp_gbp.add_resource(MPGBPMappingResourceByUUID, '/uuid/<string:uuid>')
api_mapping_mp_gbp.add_resource(MPGBPMappingResourceByModbusPointUUID, '/modbus/<string:uuid>')
api_mapping_mp_gbp.add_resource(MPGBPMappingResourceByGenericPointUUID, '/generic/<string:uuid>')
api_mapping_mp_gbp.add_resource(MPGBPMappingResourceByBACnetPointUUID, '/bacnet/<string:uuid>')

bp_sync = Blueprint('sync', __name__, url_prefix='/api/sync')
api_sync = Api(bp_sync)
api_sync.add_resource(MPToBPSync, '/mp_to_bp')

bp_system = Blueprint('system', __name__, url_prefix='/api/system')
api_system = Api(bp_system)
api_system.add_resource(GetSystemMem, '/memory')
api_system.add_resource(Ping, '/ping')

bp_schedule = Blueprint('schedules', __name__, url_prefix='/api/schedules')
api_schedule = Api(bp_schedule)
api_schedule.add_resource(ScheduleResourceList, '')
api_schedule.add_resource(ScheduleResourceByUUID, '/uuid/<string:uuid>')

bp_setting = Blueprint('settings', __name__, url_prefix='/api/settings')
api_setting = Api(bp_setting)
api_setting.add_resource(InfluxSettingResource, '/influx')
api_setting.add_resource(PostgresSettingResource, '/postgres')

