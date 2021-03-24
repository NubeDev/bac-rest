import json
import logging
import time

import schedule
from influxdb import InfluxDBClient
from registry.registry import RubixRegistry

from src import InfluxSetting
from src.handlers.exception import exception_handler
from src.models.point.model_point import PointModel
from src.models.point.model_point_store_history import PointStoreHistoryModel
from src.models.setting.model_setting_influx import InfluxSettingModel
from src.services.histories.history_binding import HistoryBinding
from src.utils import Singleton

logger = logging.getLogger(__name__)


class InfluxDB(HistoryBinding, metaclass=Singleton):

    def __init__(self):
        self.__config = None
        self.__client = None
        self.__wires_plat = None
        self.__is_connected = False
        self.__schedule_job = None
        self.__influx_setting = None

    @property
    def config(self) -> InfluxSetting:
        return self.__config

    def status(self) -> bool:
        return self.__is_connected

    def disconnect(self):
        self.__is_connected = False

    def start_influx(self, config: InfluxSetting):
        self.__config = config
        self.__influx_setting = InfluxSettingModel.create_default_if_does_not_exists(self.config)
        self.loop_forever()

    def loop_forever(self):
        while True:
            try:
                while not self.status():
                    self.connect(self.__influx_setting)
                    time.sleep(self.__influx_setting.attempt_reconnect_secs)

                if self.status():
                    if not self.__schedule_job:
                        logger.info("Registering InfluxDB for scheduler job")
                        # self.__schedule_job = schedule.every(5).seconds.do(self.sync)  # for testing
                        self.__schedule_job = schedule.every(self.__influx_setting.timer).minutes.do(self.sync)
                    schedule.run_pending()
                else:
                    logger.error("InfluxDB can't be registered with not working client details")
                time.sleep(2)
            except Exception as e:
                logger.error(e)
                logger.warning("InfluxDB is not connected, waiting for InfluxDB connection...")
                time.sleep(self.__influx_setting.attempt_reconnect_secs)

    def restart_influx(self, influx_setting):
        self.disconnect()
        if self.__schedule_job:
            schedule.clear()
        self.__reset_variable()
        self.__influx_setting = influx_setting

    def connect(self, influx_setting):
        if self.__client:
            self.__client.close()

        try:
            self.__client = InfluxDBClient(host=influx_setting.host,
                                           port=influx_setting.port,
                                           username=influx_setting.username,
                                           password=influx_setting.password,
                                           database=influx_setting.database,
                                           ssl=influx_setting.ssl,
                                           verify_ssl=influx_setting.verify_ssl,
                                           timeout=influx_setting.timeout,
                                           retries=influx_setting.retries,
                                           path=influx_setting.path)
            self.__client.ping()
            self.__is_connected = True
        except Exception as e:
            self.__is_connected = False
            logger.error(f'Connection Error: {str(e)}')

    def __reset_variable(self):
        self.__schedule_job = None
        self.__wires_plat = None

    @exception_handler
    def sync(self):
        logger.info('InfluxDB sync has is been called')
        self.__wires_plat = RubixRegistry().read_wires_plat()
        if not self.__wires_plat:
            logger.error('Please add wires-plat on Rubix Service')
            return
        self._sync()

    def _sync(self):
        store = []
        plat = {
            'client_id': self.__wires_plat.get('client_id'),
            'client_name': self.__wires_plat.get('client_name'),
            'site_id': self.__wires_plat.get('site_id'),
            'site_name': self.__wires_plat.get('site_name'),
            'device_id': self.__wires_plat.get('device_id'),
            'device_name': self.__wires_plat.get('device_name')
        }
        for point in PointModel.find_all():
            point_last_sync_id: int = self._get_point_last_sync_id(point.uuid)
            for psh in PointStoreHistoryModel.get_all_after(point_last_sync_id, point.uuid):
                tags = plat.copy()
                point_store_history: PointStoreHistoryModel = psh
                point: PointModel = point_store_history.point
                if point.tags:
                    point_tags = json.loads(point.tags)
                    # insert tags from point object
                    for point_tag in point_tags:
                        tags[point_tag] = point_tags[point_tag]
                tags.update({
                    'point_uuid': point.uuid,
                    'point_name': point.name,
                    'edge_device_uuid': point.device.uuid,
                    'edge_device_name': point.device.name,
                    'network_uuid': point.device.network.uuid,
                    'network_name': point.device.network.name,
                    'driver': point.driver.name,
                })
                fields = {
                    'id': point_store_history.id,
                    'value': point_store_history.value,
                    'value_original': point_store_history.value_original,
                    'value_raw': point_store_history.value_raw,
                    'fault': point_store_history.fault,
                    'fault_message': point_store_history.fault_message,
                }
                row = {
                    'measurement': self.__influx_setting.measurement,
                    'tags': tags,
                    'time': point_store_history.ts_value,
                    'fields': fields
                }
                store.append(row)
        if len(store):
            logger.debug(f"Storing: {store}")
            self.__client.write_points(store)
            logger.info(f'Stored {len(store)} rows on {self.__influx_setting.measurement} measurement')
        else:
            logger.debug("Nothing to store, no new records")

    def _get_point_last_sync_id(self, point_uuid):
        query = f"SELECT MAX(id), point_uuid FROM {self.__influx_setting.measurement} WHERE point_uuid='{point_uuid}'"
        result_set = self.__client.query(query)
        points = list(result_set.get_points())
        if len(points) == 0:
            last_sync_id = 0
        else:
            last_sync_id = list(result_set.get_points())[0].get('max')
        return last_sync_id
