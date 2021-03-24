import json
import logging
import time
from typing import List, Union, Dict

import psycopg2
import schedule
from psycopg2.extras import execute_values
from registry.registry import RubixRegistry

from src.handlers.exception import exception_handler
from src.models.point.model_point import PointModel
from src.models.point.model_point_store_history import PointStoreHistoryModel
from src.models.setting.model_setting_postgres import PostgresSettingModel
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
        self.__points_table_name: str = ''
        self.__points_values_table_name: str = ''
        self.__points_tags_table_name: str = ''
        self.__schedule_job = None
        self.__postgres_setting: Union[PostgresSettingModel, None] = None

    @property
    def config(self) -> Union[PostgresSetting, None]:
        return self.__config

    def status(self) -> bool:
        return self.__is_connected

    def disconnect(self):
        self.__is_connected = False

    def start_postgres(self, config: PostgresSetting):
        self.__config = config
        self.__postgres_setting = PostgresSettingModel.create_default_if_does_not_exists(self.config)
        self.__points_table_name: str = self.__postgres_setting.table_name
        self.__points_values_table_name: str = f'{self.__points_table_name}_values'
        self.__points_tags_table_name: str = f'{self.__points_table_name}_tags'
        self.loop_forever()

    def loop_forever(self):
        while True:
            try:
                while not self.status():
                    self.connect(self.__postgres_setting)
                    time.sleep(self.__postgres_setting.attempt_reconnect_secs)
                if self.status():
                    if not self.__schedule_job:
                        logger.info("Registering PostgreSQL for scheduler job")
                        # self.__schedule_job = schedule.every(5).seconds.do(self.sync)  # for testing
                        self.__schedule_job = schedule.every(self.__postgres_setting.timer).minutes.do(self.sync)
                    schedule.run_pending()
                else:
                    logger.error("PostgreSQL can't be registered with not working client details")
                time.sleep(2)
            except Exception as e:
                logger.error(e)
                logger.warning("PostgreSQL is not connected, waiting for PostgreSQL connection...")
                time.sleep(self.__postgres_setting.attempt_reconnect_secs)

    def restart_postgres(self, postgres_setting):
        self.disconnect()
        if self.__schedule_job:
            schedule.clear()
        self.__reset_variable()
        self.__postgres_setting = postgres_setting

    def connect(self, postgres_setting):
        if self.__client:
            self.__client.close()
        try:
            self.__client = psycopg2.connect(host=postgres_setting.host,
                                             port=postgres_setting.port,
                                             dbname=postgres_setting.dbname,
                                             user=postgres_setting.user,
                                             password=postgres_setting.password,
                                             sslmode=postgres_setting.ssl_mode,
                                             connect_timeout=postgres_setting.connect_timeout)
            self.__is_connected = True
            self._create_table_if_not_exists()
        except Exception as e:
            self.__is_connected = False
            logger.error(f'Connection Error: {str(e)}')

    def __reset_variable(self):
        self.__schedule_job = None
        self.__wires_plat = None

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
            _point: tuple = (self.__wires_plat.get('client_id'), self.__wires_plat.get('client_name'),
                             self.__wires_plat.get('site_id'), self.__wires_plat.get('site_name'),
                             self.__wires_plat.get('device_id'), self.__wires_plat.get('device_name'),
                             point.device.network.uuid, point.device.network.name,
                             point.device.uuid, point.device.name,
                             point.uuid, point.name,
                             point.driver.name)
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
        self._update_points_list(points_list)
        self._update_points_values(points_values_list)
        self._update_points_tags(points_tags_list)

    def _update_points_list(self, points_list):
        if len(points_list):
            logger.debug(f"Storing point_list: {points_list}")
            query_point = f'INSERT INTO {self.__points_table_name} ' \
                          f'(client_id, client_name, site_id, site_name, device_id, device_name, ' \
                          f'network_uuid, network_name, edge_device_uuid, edge_device_name, point_uuid, point_name, ' \
                          f'driver) ' \
                          f'VALUES %s ON CONFLICT (point_uuid) ' \
                          f'DO UPDATE SET ' \
                          f'client_id = excluded.client_id, ' \
                          f'client_name = excluded.client_name, ' \
                          f'site_id = excluded.site_id, ' \
                          f'site_name = excluded.site_name, ' \
                          f'device_id = excluded.device_id, ' \
                          f'device_name = excluded.device_name, ' \
                          f'network_uuid = excluded.network_uuid, ' \
                          f'network_name = excluded.network_name, ' \
                          f'edge_device_uuid = excluded.edge_device_uuid, ' \
                          f'edge_device_name = excluded.edge_device_name, ' \
                          f'point_name = excluded.point_name, ' \
                          f'driver = excluded.driver'
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
        query_point = f'CREATE TABLE IF NOT EXISTS {self.__points_table_name} ' \
                      f'(client_id VARCHAR(80), ' \
                      f'client_name VARCHAR(80), ' \
                      f'site_id VARCHAR(80), ' \
                      f'site_name VARCHAR(80), ' \
                      f'device_id VARCHAR(80), ' \
                      f'device_name VARCHAR(80),' \
                      f'network_uuid VARCHAR(80),' \
                      f'network_name VARCHAR(80), ' \
                      f'edge_device_uuid VARCHAR(80), ' \
                      f'edge_device_name VARCHAR(80), ' \
                      f'point_uuid VARCHAR PRIMARY KEY,' \
                      f'point_name VARCHAR(80), ' \
                      f'driver VARCHAR(80));'
        query_point_value_data = f'CREATE TABLE IF NOT EXISTS {self.__points_values_table_name} ' \
                                 f'(id INTEGER PRIMARY KEY, ' \
                                 f'point_uuid VARCHAR REFERENCES {self.__points_table_name} ON DELETE RESTRICT, ' \
                                 f'value NUMERIC,' \
                                 f'value_original NUMERIC, ' \
                                 f'value_raw VARCHAR, ' \
                                 f'fault BOOLEAN, ' \
                                 f'fault_message VARCHAR,' \
                                 f'ts_value  TIMESTAMP, ' \
                                 f'ts_fault TIMESTAMP,' \
                                 f'CONSTRAINT fk_{self.__points_table_name} FOREIGN KEY(point_uuid) ' \
                                 f'REFERENCES {self.__points_table_name}(point_uuid));'
        query_point_tag = f'CREATE TABLE IF NOT EXISTS {self.__points_tags_table_name} ' \
                          f'(point_uuid VARCHAR REFERENCES {self.__points_table_name} ON DELETE RESTRICT, ' \
                          f'tag_name VARCHAR, ' \
                          f'tag_value VARCHAR,' \
                          f'PRIMARY KEY (point_uuid, tag_name));'
        with self.__client:
            with self.__client.cursor() as curs:
                try:
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
