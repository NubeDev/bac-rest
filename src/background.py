import logging
from threading import Thread

from flask import current_app
from gevent import thread
from mrb.brige import MqttRestBridge

from .setting import AppSetting

logger = logging.getLogger(__name__)


class FlaskThread(Thread):
    """
    To make every new thread behinds Flask app context.
    Maybe using another lightweight solution but richer: APScheduler <https://github.com/agronholm/apscheduler>
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = current_app._get_current_object()

    def run(self):
        with self.app.app_context():
            super().run()


class Background:

    @staticmethod
    def run():
        setting: AppSetting = current_app.config[AppSetting.KEY]

        # Services
        logger.info("Starting Services...")
        if setting.services.mqtt:
            from src.services.mqtt_client import MqttClient
            for config in setting.mqtt_settings:
                if not config.enabled:
                    continue
                mqtt_client = MqttClient()
                FlaskThread(target=mqtt_client.start, daemon=True, kwargs={'config': config}).start()

        if setting.services.histories:
            from src.services.histories.history_local import HistoryLocal
            FlaskThread(target=HistoryLocal().sync_interval, daemon=True).start()

        if setting.services.cleaner:
            from src.services.histories.point_store_history_cleaner import PointStoreHistoryCleaner
            FlaskThread(target=PointStoreHistoryCleaner().setup, daemon=True,
                        kwargs={'config': setting.cleaner}).start()

        if setting.services.history_sync_influxdb:
            from src.services.histories.sync.influxdb import InfluxDB
            FlaskThread(target=InfluxDB().start_influx, daemon=True,
                        kwargs={'config': setting.influx}).start()

        if setting.services.history_sync_postgres:
            from src.services.histories.sync.postgresql import PostgreSQL
            FlaskThread(target=PostgreSQL().start_postgres, daemon=True,
                        kwargs={'config': setting.postgres}).start()

        # Drivers
        thread.sleep(5)
        logger.info("Starting Drivers...")
        if setting.drivers.modbus_tcp:
            from src.drivers.modbus.services.polling.modbus_polling import TcpPolling, ModbusTcpRegistry
            ModbusTcpRegistry().register()
            FlaskThread(target=TcpPolling().polling, daemon=True).start()

        if setting.drivers.modbus_rtu:
            from src.drivers.modbus.services.polling.modbus_polling import RtuPolling, ModbusRtuRegistry
            ModbusRtuRegistry().register()
            FlaskThread(target=RtuPolling().polling, daemon=True).start()

        # Sync
        logger.info("Starting Sync Services...")
        if setting.drivers.bridge and setting.mqtt_rest_bridge_setting.enabled:
            FlaskThread(target=MqttRestBridge(port=setting.port, identifier=setting.identifier, prod=setting.prod,
                                              mqtt_setting=setting.mqtt_rest_bridge_setting,
                                              callback=Background.sync_on_start).start, daemon=True).start()

        if setting.services.mqtt and any(config.enabled for config in setting.mqtt_settings):
            from src.services.points_registry import PointsRegistry
            FlaskThread(target=PointsRegistry().register, daemon=True).start()
            from src.services.schedules_registry import SchedulesRegistry
            FlaskThread(target=SchedulesRegistry().register, daemon=True).start()

    @staticmethod
    def sync_on_start():
        from mrb.mapper import api_to_topic_mapper
        from mrb.message import HttpMethod
        from .models.point.model_point_store import PointStoreModel

        """Sync mapped points values from LoRa > Generic points values"""
        FlaskThread(target=api_to_topic_mapper, kwargs={'api': "/api/sync/lp_to_gp", 'destination_identifier': 'lora',
                                                        'http_method': HttpMethod.GET}).start()

        """Sync mapped points values from BACnet > Generic points values"""
        FlaskThread(target=api_to_topic_mapper, kwargs={'api': "/api/sync/bp_to_gp", 'destination_identifier': 'bacnet',
                                                        'http_method': HttpMethod.GET}).start()
        """Sync mapped points values from Modbus > Generic | BACnet points values"""
        PointStoreModel.sync_points_values_mp_to_gbp_process(force_sync=True)
