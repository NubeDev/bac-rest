import json
import logging
import time
from typing import List, Union, Dict

import psycopg2
import schedule
from psycopg2.extras import execute_values
from registry.registry import RubixRegistry

from src.drivers.generic.models.device import GenericDeviceModel
from src.drivers.generic.models.network import GenericNetworkModel
from src.drivers.modbus.models.device import ModbusDeviceModel
from src.drivers.modbus.models.network import ModbusNetworkModel
from src.handlers.exception import exception_handler
from src.models.device.model_device import DeviceModel
from src.models.network.model_network import NetworkModel
from src.models.point.model_point import PointModel
from src.models.point.model_point_store_history import PointStoreHistoryModel
from src.services.histories.history_binding import HistoryBinding
from src.setting import PostgresSetting
from src.utils import Singleton
from src.utils.string import rreplace

logger = logging.getLogger(__name__)


class PostgreSQL(HistoryBinding, metaclass=Singleton):

    def __init__(self):
        self.__config: Union[PostgresSetting, None] = None
        self.__client = None
        self.__wires_plat: Union[Dict, None] = None
        self.__is_connected = False
        self.__wires_plat_table_name: str = ''
        self.__networks_table_name: str = ''
        self.__modbus_networks_table_name: str = ''
        self.__devices_table_name: str = ''
        self.__modbus_devices_table_name: str = ''
        self.__points_table_name: str = ''
        self.__points_values_table_name: str = ''
        self.__points_tags_table_name: str = ''
        self.__generic_network_tags_table_name: str = ''
        self.__generic_device_tags_table_name: str = ''

    @property
    def config(self) -> Union[PostgresSetting, None]:
        return self.__config

    def status(self) -> bool:
        return self.__is_connected

    def disconnect(self):
        self.__is_connected = False

    def setup(self, config: PostgresSetting):
        self.__config = config
        self.__wires_plat_table_name: str = f'{self.config.table_prefix}_wires_plats'
        self.__networks_table_name: str = f'{self.config.table_prefix}_networks'
        self.__modbus_networks_table_name: str = f'{self.config.table_prefix}_modbus_networks'
        self.__devices_table_name: str = f'{self.config.table_prefix}_devices'
        self.__modbus_devices_table_name = f'{self.config.table_prefix}_modbus_devices'
        self.__points_table_name: str = f'{self.config.table_prefix}_points'
        self.__points_values_table_name: str = f'{self.__points_table_name}_values'
        self.__points_tags_table_name: str = f'{self.__points_table_name}_tags'
        self.__generic_network_tags_table_name: str = f'{self.config.table_prefix}_generic_network_tags'
        self.__generic_device_tags_table_name: str = f'{self.config.table_prefix}_generic_device_tags'

        while not self.status():
            self.connect()
            time.sleep(self.config.attempt_reconnect_secs)
        if self.status():
            logger.info("Registering PostgreSQL for scheduler job")
            # schedule.every(5).seconds.do(self.sync)  # for testing
            schedule.every(self.config.timer).minutes.do(self.sync)
            while True:
                schedule.run_pending()
                time.sleep(1)
        else:
            logger.error("PostgreSQL can't be registered with not working client details")

    def connect(self):
        if self.__client:
            self.__client.close()
        try:
            self.__client = psycopg2.connect(host=self.config.host,
                                             port=self.config.port,
                                             dbname=self.config.dbname,
                                             user=self.config.user,
                                             password=self.config.password,
                                             sslmode=self.config.ssl_mode,
                                             connect_timeout=self.config.connect_timeout)
            self.__is_connected = True
            self._create_table_if_not_exists()
        except Exception as e:
            self.__is_connected = False
            logger.error(f'Connection Error: {str(e)}')

    @exception_handler
    def sync(self):
        logger.info('PostgreSQL sync has is been called')
        self.__wires_plat = RubixRegistry().read_wires_plat()
        if not self.__wires_plat:
            logger.error('Please add wires-plat on Rubix Service')
            return
        self._sync()

    def _sync(self):
        points_list: List[tuple] = []
        points_values_list: List[tuple] = []
        points_tags_list: List[tuple] = []

        for point in PointModel.find_all():
            point_last_sync_id: int = self._get_point_last_sync_id(point.uuid)
            _point: tuple = (point.device.network.uuid, point.device.uuid,
                             point.uuid, point.driver.name, point.name)
            points_list.append(_point)

            if point.tags:
                point_tags: dict = json.loads(point.tags)
                # insert tags from point object
                for point_tag in point_tags.keys():
                    points_tags_list.append((point.uuid, point_tag, point_tags[point_tag]))

            for psh in PointStoreHistoryModel.get_all_after(point_last_sync_id, point.uuid):
                point_store_history: PointStoreHistoryModel = psh
                point_value_data: tuple = (point_store_history.id, point_store_history.point_uuid,
                                           point_store_history.value, point_store_history.value_original,
                                           point_store_history.value_raw,
                                           point_store_history.fault, point_store_history.fault_message,
                                           point_store_history.ts_value, point_store_history.ts_fault)
                points_values_list.append(point_value_data)

        self._update_wires_plats()
        self._update_networks()
        self._update_modbus_networks()
        self._update_devices()
        self._update_modbus_devices()
        self._update_generic_network_tags()
        self._update_generic_device_tags()
        self._update_points_list(points_list)
        self._update_points_values(points_values_list)
        self._update_points_tags(points_tags_list)

    def _update_wires_plats(self):
        if self.__wires_plat:
            logger.debug(f"Storing wires_plat: {self.__wires_plat}")
            query_wires_plat = f'INSERT INTO {self.__wires_plat_table_name} ' \
                               f'(global_uuid , client_id, client_name, site_id, site_name, device_id, device_name, ' \
                               f'site_address, site_city, site_state, site_zip, site_country, site_lat, site_lon, ' \
                               f'time_zone, ' \
                               f'created_on, updated_on) ' \
                               f'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ' \
                               f'ON CONFLICT (global_uuid) DO UPDATE SET ' \
                               f'client_id = excluded.client_id,' \
                               f'client_name = excluded.client_name,' \
                               f'site_id = excluded.site_id,' \
                               f'site_name = excluded.site_name,' \
                               f'device_id = excluded.device_id,' \
                               f'device_name = excluded.device_name,' \
                               f'site_address = excluded.site_address,' \
                               f'site_city = excluded.site_city,' \
                               f'site_state = excluded.site_state,' \
                               f'site_zip = excluded.site_zip,' \
                               f'site_country = excluded.site_country,' \
                               f'site_lat = excluded.site_lat,' \
                               f'site_lon = excluded.site_lon,' \
                               f'time_zone = excluded.time_zone,' \
                               f'created_on = excluded.created_on,' \
                               f'updated_on = excluded.updated_on'
            with self.__client:
                with self.__client.cursor() as curs:
                    try:
                        wires_plat: tuple = (self.__wires_plat.get('global_uuid'),
                                             self.__wires_plat.get('client_id'), self.__wires_plat.get('client_name'),
                                             self.__wires_plat.get('site_id'), self.__wires_plat.get('site_name'),
                                             self.__wires_plat.get('device_id'), self.__wires_plat.get('device_name'),
                                             self.__wires_plat.get('site_address'), self.__wires_plat.get('site_city'),
                                             self.__wires_plat.get('site_state'), self.__wires_plat.get('site_zip'),
                                             self.__wires_plat.get('site_country'), self.__wires_plat.get('site_lat'),
                                             self.__wires_plat.get('site_lon'), self.__wires_plat.get('time_zone'),
                                             self.__wires_plat.get('created_on'),
                                             self.__wires_plat.get('updated_on'))
                        curs.execute(query_wires_plat, wires_plat)

                    except psycopg2.Error as e:
                        logger.error(str(e))
            logger.info(f'Stored/updated 1 rows on {self.__wires_plat_table_name} table')
        else:
            logger.debug(f"Nothing to store on {self.__wires_plat_table_name}")

    def _update_networks(self):
        networks_list: List[tuple] = []
        for network in NetworkModel.find_all():
            networks_list.append((network.uuid, network.name, network.enable, network.fault, network.history_enable,
                                  network.driver.name, network.created_on, network.updated_on,
                                  self.__wires_plat.get('global_uuid')))
        if len(networks_list):
            logger.debug(f"Storing networks_list: {networks_list}")
            query_network = f'INSERT INTO {self.__networks_table_name} ' \
                            f'(uuid, name, enable, fault, history_enable, driver, created_on, updated_on, ' \
                            f'wires_plat_global_uuid) ' \
                            f'VALUES %s ON CONFLICT (uuid) ' \
                            f'DO UPDATE SET ' \
                            f'name = excluded.name, ' \
                            f'enable = excluded.enable, ' \
                            f'fault = excluded.fault, ' \
                            f'history_enable = excluded.history_enable, ' \
                            f'driver = excluded.driver, ' \
                            f'created_on = excluded.created_on, ' \
                            f'updated_on = excluded.updated_on, ' \
                            f'wires_plat_global_uuid = excluded.wires_plat_global_uuid'
            with self.__client:
                with self.__client.cursor() as curs:
                    try:
                        execute_values(curs, query_network, networks_list)
                    except psycopg2.Error as e:
                        logger.error(str(e))
            logger.info(f'Stored/updated {len(networks_list)} rows on {self.__networks_table_name} table')
        else:
            logger.debug(f"Nothing to store on {self.__networks_table_name}")

    def _update_modbus_networks(self):
        modbus_networks_list: List[tuple] = []
        for network in ModbusNetworkModel.find_all():
            modbus_networks_list.append((network.uuid, network.rtu_port, network.rtu_speed, network.rtu_stop_bits,
                                         network.rtu_parity.name, network.rtu_byte_size, network.tcp_ip,
                                         network.tcp_port, network.type.name, network.timeout,
                                         network.polling_interval_runtime, network.point_interval_ms_between_points))
        if len(modbus_networks_list):
            logger.debug(f"Storing modbus_networks_list: {modbus_networks_list}")
            query_modbus_network = f'INSERT INTO {self.__modbus_networks_table_name} ' \
                                   f'(uuid, rtu_port, rtu_speed, rtu_stop_bits, rtu_parity, rtu_byte_size, tcp_ip, ' \
                                   f'tcp_port, type, timeout, polling_interval_runtime, ' \
                                   f'point_interval_ms_between_points) ' \
                                   f'VALUES %s ON CONFLICT (uuid) ' \
                                   f'DO UPDATE SET ' \
                                   f'rtu_port = excluded.rtu_port, ' \
                                   f'rtu_speed = excluded.rtu_speed, ' \
                                   f'rtu_stop_bits = excluded.rtu_stop_bits, ' \
                                   f'rtu_parity = excluded.rtu_parity, ' \
                                   f'rtu_byte_size = excluded.rtu_byte_size, ' \
                                   f'tcp_ip = excluded.tcp_ip, ' \
                                   f'tcp_port = excluded.tcp_port,' \
                                   f'type = excluded.type,' \
                                   f'timeout = excluded.timeout,' \
                                   f'polling_interval_runtime = excluded.polling_interval_runtime,' \
                                   f'point_interval_ms_between_points = excluded.point_interval_ms_between_points'
            with self.__client:
                with self.__client.cursor() as curs:
                    try:
                        execute_values(curs, query_modbus_network, modbus_networks_list)
                    except psycopg2.Error as e:
                        logger.error(str(e))
            logger.info(f'Stored/updated {len(modbus_networks_list)} rows on {self.__modbus_networks_table_name} table')
        else:
            logger.debug(f"Nothing to store on {self.__modbus_networks_table_name}")

    def _update_devices(self):
        devices_list: List[tuple] = []
        for device in DeviceModel.find_all():
            devices_list.append((device.uuid, device.network_uuid, device.name, device.enable, device.fault,
                                 device.history_enable, device.driver.name, device.created_on, device.updated_on))
        if len(devices_list):
            logger.debug(f"Storing devices_list: {devices_list}")
            query_network = f'INSERT INTO {self.__devices_table_name} ' \
                            f'(uuid, network_uuid, name, enable, fault, history_enable, driver, created_on, ' \
                            f'updated_on) ' \
                            f'VALUES %s ON CONFLICT (uuid) ' \
                            f'DO UPDATE SET ' \
                            f'network_uuid = excluded.network_uuid, ' \
                            f'name = excluded.name, ' \
                            f'enable = excluded.enable, ' \
                            f'fault = excluded.fault, ' \
                            f'history_enable = excluded.history_enable, ' \
                            f'driver = excluded.driver, ' \
                            f'created_on = excluded.created_on, ' \
                            f'updated_on = excluded.updated_on'
            with self.__client:
                with self.__client.cursor() as curs:
                    try:
                        execute_values(curs, query_network, devices_list)
                    except psycopg2.Error as e:
                        logger.error(str(e))
            logger.info(f'Stored/updated {len(devices_list)} rows on {self.__devices_table_name} table')
        else:
            logger.debug(f"Nothing to store on {self.__devices_table_name}")

    def _update_modbus_devices(self):
        modbus_devices_list: List[tuple] = []
        for device in ModbusDeviceModel.find_all():
            modbus_devices_list.append((device.uuid, device.type.name, device.address, device.zero_based,
                                        device.ping_point, device.supports_multiple_rw,
                                        device.modbus_network_uuid_constraint))
        if len(modbus_devices_list):
            logger.debug(f"Storing modbus_devices_list: {modbus_devices_list}")
            query_modbus_device = f'INSERT INTO {self.__modbus_devices_table_name} ' \
                                  f'(uuid, type, address, zero_based, ping_point, supports_multiple_rw, ' \
                                  f'modbus_network_uuid_constraint) ' \
                                  f'VALUES %s ON CONFLICT (uuid) ' \
                                  f'DO UPDATE SET ' \
                                  f'type = excluded.type, ' \
                                  f'address = excluded.address, ' \
                                  f'zero_based = excluded.zero_based, ' \
                                  f'ping_point = excluded.ping_point, ' \
                                  f'supports_multiple_rw = excluded.supports_multiple_rw, ' \
                                  f'modbus_network_uuid_constraint = excluded.modbus_network_uuid_constraint'
            with self.__client:
                with self.__client.cursor() as curs:
                    try:
                        execute_values(curs, query_modbus_device, modbus_devices_list)
                    except psycopg2.Error as e:
                        logger.error(str(e))
            logger.info(f'Stored/updated {len(modbus_devices_list)} rows on {self.__modbus_devices_table_name} table')
        else:
            logger.debug(f"Nothing to store on {self.__modbus_devices_table_name}")

    def _update_generic_network_tags(self):
        generic_network_tags_list: List[tuple] = []
        for generic_network in GenericNetworkModel.find_all():
            if generic_network.tags:
                generic_network_tags: dict = json.loads(generic_network.tags)
                # insert tags from generic_network object
                for generic_network_tag in generic_network_tags.keys():
                    generic_network_tags_list.append((generic_network.uuid, generic_network_tag,
                                                      generic_network_tags[generic_network_tag]))
        if len(generic_network_tags_list):
            logger.debug(f"Storing generic_network_tags_list: {generic_network_tags_list}")
            query_generic_network_tag = f'INSERT INTO {self.__generic_network_tags_table_name} ' \
                                        f'(uuid, tag_name, tag_value) ' \
                                        f'VALUES %s ON CONFLICT (uuid, tag_name) ' \
                                        f'DO UPDATE SET tag_value = excluded.tag_value'
            with self.__client:
                with self.__client.cursor() as curs:
                    try:
                        if len(generic_network_tags_list):
                            # Remove comma (,) from ('<uuid>',)
                            in_uuid: str = rreplace(str(tuple(i[0] for i in generic_network_tags_list)), ",)", ")",
                                                    1)
                            in_tags_list: str = rreplace(
                                str(tuple((i[0], i[1]) for i in generic_network_tags_list)), ",)", ")", 1)
                            query_delete_generic_network_tag = f'DELETE FROM {self.__generic_network_tags_table_name} ' \
                                                               f'WHERE uuid IN {in_uuid} ' \
                                                               f'AND (uuid, tag_name) NOT IN {in_tags_list}'
                            curs.execute(query_delete_generic_network_tag)
                        execute_values(curs, query_generic_network_tag, generic_network_tags_list)
                    except psycopg2.Error as e:
                        logger.error(str(e))
            logger.info(f'Stored/updated {len(generic_network_tags_list)} rows on '
                        f'{self.__generic_network_tags_table_name} table')
        else:
            logger.debug(f"Nothing to store on {self.__generic_network_tags_table_name}")

    def _update_generic_device_tags(self):
        generic_device_tags_list: List[tuple] = []
        for generic_device in GenericDeviceModel.find_all():
            if generic_device.tags:
                generic_device_tags: dict = json.loads(generic_device.tags)
                # insert tags from generic_device object
                for generic_device_tag in generic_device_tags.keys():
                    generic_device_tags_list.append((generic_device.uuid, generic_device_tag,
                                                     generic_device_tags[generic_device_tag]))
        if len(generic_device_tags_list):
            logger.debug(f"Storing generic_device_tags_list: {generic_device_tags_list}")
            query_generic_device_tag = f'INSERT INTO {self.__generic_device_tags_table_name} ' \
                                       f'(uuid, tag_name, tag_value) ' \
                                       f'VALUES %s ON CONFLICT (uuid, tag_name) ' \
                                       f'DO UPDATE SET tag_value = excluded.tag_value'
            with self.__client:
                with self.__client.cursor() as curs:
                    try:
                        if len(generic_device_tags_list):
                            # Remove comma (,) from ('<uuid>',)
                            in_uuid: str = rreplace(str(tuple(i[0] for i in generic_device_tags_list)), ",)", ")",
                                                    1)
                            in_tags_list: str = rreplace(
                                str(tuple((i[0], i[1]) for i in generic_device_tags_list)), ",)", ")", 1)
                            query_delete_generic_device_tag = f'DELETE FROM {self.__generic_device_tags_table_name} ' \
                                                              f'WHERE uuid IN {in_uuid} ' \
                                                              f'AND (uuid, tag_name) NOT IN {in_tags_list}'
                            curs.execute(query_delete_generic_device_tag)
                        execute_values(curs, query_generic_device_tag, generic_device_tags_list)
                    except psycopg2.Error as e:
                        logger.error(str(e))
            logger.info(f'Stored/updated {len(generic_device_tags_list)} rows on '
                        f'{self.__generic_device_tags_table_name} table')
        else:
            logger.debug(f"Nothing to store on {self.__generic_device_tags_table_name}")

    def _update_points_list(self, points_list):
        if len(points_list):
            logger.debug(f"Storing point_list: {points_list}")
            query_point = f'INSERT INTO {self.__points_table_name} ' \
                          f'(network_uuid, device_uuid, point_uuid, driver, name) ' \
                          f'VALUES %s ON CONFLICT (point_uuid) ' \
                          f'DO UPDATE SET ' \
                          f'network_uuid = excluded.network_uuid, ' \
                          f'device_uuid = excluded.device_uuid, ' \
                          f'driver = excluded.driver,' \
                          f'name = excluded.name'
            with self.__client:
                with self.__client.cursor() as curs:
                    try:
                        execute_values(curs, query_point, points_list)
                    except psycopg2.Error as e:
                        logger.error(str(e))
            logger.info(f'Stored/updated {len(points_list)} rows on {self.__points_table_name} table')
        else:
            logger.debug(f"Nothing to store on {self.__points_table_name}")

    def _update_points_values(self, points_values_list):
        if len(points_values_list):
            logger.debug(f"Storing point_value_data_list: {points_values_list}")
            query_point_value_data = f'INSERT INTO {self.__points_values_table_name} ' \
                                     f'(id, point_uuid, value, value_original, value_raw, fault, fault_message, ' \
                                     f'ts_value, ts_fault) ' \
                                     f'VALUES %s ON CONFLICT (id) DO NOTHING'
            with self.__client:
                with self.__client.cursor() as curs:
                    try:
                        execute_values(curs, query_point_value_data, points_values_list)
                    except psycopg2.Error as e:
                        logger.error(str(e))
            logger.info(f'Stored {len(list(set(points_values_list)))} rows on {self.__points_values_table_name} table')
        else:
            logger.debug(f"Nothing to store on {self.__points_values_table_name}, no new records")

    def _update_points_tags(self, points_tags_list):
        if len(points_tags_list):
            logger.debug(f"Storing point_tag_list: {points_tags_list}")
            query_point_tag = f'INSERT INTO {self.__points_tags_table_name} ' \
                              f'(point_uuid, tag_name, tag_value) ' \
                              f'VALUES %s ON CONFLICT (point_uuid, tag_name) ' \
                              f'DO UPDATE SET tag_value = excluded.tag_value'
            with self.__client:
                with self.__client.cursor() as curs:
                    try:
                        if len(points_tags_list):
                            # Remove comma (,) from ('<uuid>',)
                            in_point_uuid: str = rreplace(str(tuple(i[0] for i in points_tags_list)), ",)", ")", 1)
                            in_point_tags_list: str = rreplace(
                                str(tuple((i[0], i[1]) for i in points_tags_list)), ",)", ")", 1)
                            query_delete_point_tag = f'DELETE FROM {self.__points_tags_table_name} ' \
                                                     f'WHERE point_uuid IN {in_point_uuid} ' \
                                                     f'AND (point_uuid, tag_name) NOT IN {in_point_tags_list}'
                            curs.execute(query_delete_point_tag)
                        execute_values(curs, query_point_tag, points_tags_list)
                    except psycopg2.Error as e:
                        logger.error(str(e))
            logger.info(f'Stored/updated {len(points_tags_list)} rows on {self.__points_tags_table_name} table')
        else:
            logger.debug(f"Nothing to store on {self.__points_tags_table_name}")

    def _create_table_if_not_exists(self):
        query_wires_plat = f'CREATE TABLE IF NOT EXISTS {self.__wires_plat_table_name} ' \
                           f'(global_uuid VARCHAR PRIMARY KEY,' \
                           f'client_id VARCHAR,' \
                           f'client_name VARCHAR,' \
                           f'site_id VARCHAR,' \
                           f'site_name VARCHAR,' \
                           f'device_id VARCHAR,' \
                           f'device_name VARCHAR,' \
                           f'site_address VARCHAR,' \
                           f'site_city VARCHAR,' \
                           f'site_state VARCHAR,' \
                           f'site_zip VARCHAR,' \
                           f'site_country VARCHAR,' \
                           f'site_lat VARCHAR,' \
                           f'site_lon VARCHAR,' \
                           f'time_zone VARCHAR,' \
                           f'created_on TIMESTAMP,' \
                           f'updated_on TIMESTAMP);'
        query_network = f'CREATE TABLE IF NOT EXISTS {self.__networks_table_name} ' \
                        f'(uuid VARCHAR PRIMARY KEY,' \
                        f'name VARCHAR,' \
                        f'enable BOOLEAN,' \
                        f'fault BOOLEAN,' \
                        f'history_enable BOOLEAN,' \
                        f'driver VARCHAR,' \
                        f'created_on TIMESTAMP,' \
                        f'updated_on TIMESTAMP,' \
                        f'wires_plat_global_uuid VARCHAR,' \
                        f'CONSTRAINT fk_{self.__wires_plat_table_name} FOREIGN KEY(wires_plat_global_uuid) ' \
                        f'REFERENCES {self.__wires_plat_table_name}(global_uuid) ON DELETE RESTRICT);'
        query_modbus_network = f'CREATE TABLE IF NOT EXISTS {self.__modbus_networks_table_name} ' \
                               f'(uuid VARCHAR PRIMARY KEY,' \
                               f'rtu_port VARCHAR,' \
                               f'rtu_speed NUMERIC,' \
                               f'rtu_stop_bits NUMERIC,' \
                               f'rtu_parity VARCHAR,' \
                               f'rtu_byte_size NUMERIC,' \
                               f'tcp_ip VARCHAR,' \
                               f'tcp_port NUMERIC,' \
                               f'type VARCHAR,' \
                               f'timeout NUMERIC,' \
                               f'polling_interval_runtime NUMERIC,' \
                               f'point_interval_ms_between_points NUMERIC,' \
                               f'CONSTRAINT fk_{self.__networks_table_name} FOREIGN KEY(uuid) ' \
                               f'REFERENCES {self.__networks_table_name}(uuid) ON DELETE RESTRICT);'
        query_generic_network_tag = f'CREATE TABLE IF NOT EXISTS {self.__generic_network_tags_table_name} ' \
                                    f'(uuid VARCHAR,' \
                                    f'tag_name VARCHAR, ' \
                                    f'tag_value VARCHAR,' \
                                    f'PRIMARY KEY (uuid, tag_name),' \
                                    f'CONSTRAINT fk_{self.__networks_table_name} FOREIGN KEY(uuid) ' \
                                    f'REFERENCES {self.__networks_table_name}(uuid) ON DELETE RESTRICT);'
        query_device = f'CREATE TABLE IF NOT EXISTS {self.__devices_table_name} ' \
                       f'(uuid VARCHAR PRIMARY KEY,' \
                       f'network_uuid VARCHAR,' \
                       f'name VARCHAR,' \
                       f'enable BOOLEAN,' \
                       f'fault BOOLEAN,' \
                       f'history_enable BOOLEAN,' \
                       f'driver VARCHAR,' \
                       f'created_on TIMESTAMP,' \
                       f'updated_on TIMESTAMP,' \
                       f'CONSTRAINT fk_{self.__networks_table_name} FOREIGN KEY(network_uuid) ' \
                       f'REFERENCES {self.__networks_table_name}(uuid) ON DELETE RESTRICT);'
        query_modbus_device = f'CREATE TABLE IF NOT EXISTS {self.__modbus_devices_table_name} ' \
                              f'(uuid VARCHAR PRIMARY KEY,' \
                              f'type VARCHAR,' \
                              f'address NUMERIC,' \
                              f'zero_based BOOLEAN,' \
                              f'ping_point VARCHAR,' \
                              f'supports_multiple_rw BOOLEAN,' \
                              f'modbus_network_uuid_constraint VARCHAR,' \
                              f'CONSTRAINT fk_{self.__devices_table_name} FOREIGN KEY(uuid) ' \
                              f'REFERENCES {self.__devices_table_name}(uuid) ON DELETE RESTRICT);'
        query_generic_device_tag = f'CREATE TABLE IF NOT EXISTS {self.__generic_device_tags_table_name} ' \
                                   f'(uuid VARCHAR,' \
                                   f'tag_name VARCHAR, ' \
                                   f'tag_value VARCHAR,' \
                                   f'PRIMARY KEY (uuid, tag_name),' \
                                   f'CONSTRAINT fk_{self.__devices_table_name} FOREIGN KEY(uuid) ' \
                                   f'REFERENCES {self.__devices_table_name}(uuid) ON DELETE RESTRICT);'
        query_point = f'CREATE TABLE IF NOT EXISTS {self.__points_table_name} ' \
                      f'(network_uuid VARCHAR(80),' \
                      f'device_uuid VARCHAR(80), ' \
                      f'point_uuid VARCHAR PRIMARY KEY,' \
                      f'driver VARCHAR(80),' \
                      f'name VARCHAR,' \
                      f'CONSTRAINT fk_{self.__networks_table_name} FOREIGN KEY(network_uuid) ' \
                      f'REFERENCES {self.__networks_table_name}(uuid) ON DELETE RESTRICT, ' \
                      f'CONSTRAINT fk_{self.__devices_table_name} FOREIGN KEY(device_uuid) ' \
                      f'REFERENCES {self.__devices_table_name}(uuid) ON DELETE RESTRICT);'
        query_point_value_data = f'CREATE TABLE IF NOT EXISTS {self.__points_values_table_name} ' \
                                 f'(id INTEGER PRIMARY KEY, ' \
                                 f'point_uuid VARCHAR, ' \
                                 f'value NUMERIC,' \
                                 f'value_original NUMERIC, ' \
                                 f'value_raw VARCHAR, ' \
                                 f'fault BOOLEAN, ' \
                                 f'fault_message VARCHAR,' \
                                 f'ts_value  TIMESTAMP, ' \
                                 f'ts_fault TIMESTAMP,' \
                                 f'CONSTRAINT fk_{self.__points_table_name} FOREIGN KEY(point_uuid) ' \
                                 f'REFERENCES {self.__points_table_name}(point_uuid) ON DELETE RESTRICT);'
        query_point_tag = f'CREATE TABLE IF NOT EXISTS {self.__points_tags_table_name} ' \
                          f'(point_uuid VARCHAR REFERENCES {self.__points_table_name} ON DELETE RESTRICT, ' \
                          f'tag_name VARCHAR, ' \
                          f'tag_value VARCHAR,' \
                          f'PRIMARY KEY (point_uuid, tag_name));'
        with self.__client:
            with self.__client.cursor() as curs:
                try:
                    curs.execute(query_wires_plat)
                    curs.execute(query_network)
                    curs.execute(query_modbus_network)
                    curs.execute(query_device)
                    curs.execute(query_modbus_device)
                    curs.execute(query_generic_network_tag)
                    curs.execute(query_generic_device_tag)
                    curs.execute(query_point)
                    curs.execute(query_point_value_data)
                    curs.execute(query_point_tag)
                except psycopg2.Error as e:
                    logger.error(str(e))

    def _get_point_last_sync_id(self, point_uuid):
        query = f"SELECT MAX(id) FROM {self.__points_values_table_name} WHERE point_uuid=%s;"
        with self.__client:
            with self.__client.cursor() as curs:
                curs.execute(query, (point_uuid,))
                last_sync_id = curs.fetchone()[0]
                if last_sync_id:
                    return last_sync_id
                return 0
