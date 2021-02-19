import json
import logging

from registry.registry import RubixRegistry

from src.models.model_base import ModelBase
from src.models.point.model_point import PointModel
from src.models.point.model_point_store import PointStoreModel
from src.services.event_service_base import EventServiceBase, Event, EventType
from src.utils.model_utils import datetime_to_str
from .mqtt_client_base import MqttClientBase
from .mqtt_registry import MqttRegistry
from ...setting import MqttSettingBase, MqttSetting

logger = logging.getLogger(__name__)

SERVICE_NAME_MQTT_CLIENT = 'mqtt'

MQTT_TOPIC_ALL = 'all'
MQTT_TOPIC_DRIVER = 'driver'
MQTT_TOPIC_UPDATE = 'update'
MQTT_TOPIC_UPDATE_POINT = 'point'
MQTT_TOPIC_UPDATE_DEVICE = 'device'
MQTT_TOPIC_UPDATE_NETWORK = 'network'
MQTT_TOPIC_COV = 'cov'
MQTT_TOPIC_COV_ALL = 'all'
MQTT_TOPIC_COV_VALUE = 'value'


class MqttClient(MqttClientBase, EventServiceBase):
    def __init__(self):
        MqttClientBase.__init__(self)
        EventServiceBase.__init__(self, SERVICE_NAME_MQTT_CLIENT, False)
        self.supported_events[EventType.POINT_COV] = True
        self.supported_events[EventType.POINT_UPDATE] = True
        self.supported_events[EventType.DEVICE_UPDATE] = True
        self.supported_events[EventType.NETWORK_UPDATE] = True
        self.supported_events[EventType.MQTT_DEBUG] = True

    @property
    def config(self) -> MqttSetting:
        return self._config

    def start(self, config: MqttSettingBase):
        from src.event_dispatcher import EventDispatcher
        EventDispatcher().add_service(self)
        MqttRegistry().add(self)
        super(MqttClient, self).start(config)

    def publish_cov(self, source_driver: str, network_uuid: str, network_name: str, device_uuid: str, device_name: str,
                    point: PointModel, point_store: PointStoreModel):
        if not self.status():
            logger.error(f"MQTT client {self.to_string()} is not connected...")
            return
        if point is None or point_store is None or device_uuid is None or network_uuid is None or source_driver is \
                None or network_name is None or device_name is None:
            raise Exception('Invalid MQTT publish arguments')

        if point_store.fault:
            payload: dict = {
                'fault': point_store.fault,
                'fault_message': point_store.fault_message,
                'ts': point_store.ts_fault,
            }
        else:
            payload: dict = {
                'fault': point_store.fault,
                'value': point_store.value,
                'value_raw': point_store.value_raw,
                'ts': point_store.ts_value,
            }
        if not isinstance(payload['ts'], str):
            payload['ts'] = datetime_to_str(payload['ts'])

        topic: str = self.make_topic(
            (self.config.topic, MQTT_TOPIC_COV, MQTT_TOPIC_COV_ALL, source_driver, network_uuid, network_name,
             device_uuid, device_name, point.uuid, point.name))
        if not topic:
            logger.error('Please add wires-plat on Rubix Service')
            return
        logger.debug(f'MQTT PUB: {self.to_string()} {topic} > {payload}')
        self._client.publish(topic, json.dumps(payload), self.config.qos, self.config.retain)

        if self.config.publish_value and not point_store.fault:
            topic: str = self.make_topic(
                (self.config.topic, MQTT_TOPIC_COV, MQTT_TOPIC_COV_VALUE, source_driver, network_uuid, network_name,
                 device_uuid, device_name, point.uuid, point.name))
            logger.debug(f'MQTT PUB: {self.to_string()} {topic} > {point_store.value}')
            self._client.publish(topic, point_store.value, self.config.qos, self.config.retain)

    def publish_update(self, model: ModelBase, updates: dict):
        if not self.status():
            logger.error(f"MQTT client {self.to_string()} is not connected...")
            return
        if model is None or updates is None or len(updates) == 0:
            raise Exception('Invalid MQTT publish arguments')

        topic: str = self.make_topic((self.config.topic, MQTT_TOPIC_UPDATE, model.get_model_event_name(), model.uuid))
        if not topic:
            logger.error('Please add wires-plat on Rubix Service')
            return
        logger.debug(f'MQTT PUB: {self.to_string()} {topic} > {updates}')
        self._client.publish(topic, json.dumps(updates), self.config.qos, self.config.retain)

    def publish_debug_message(self, topic: str, message: str):
        if not self.status():
            logger.error(f"MQTT client {self.to_string()} is not connected...")
            return
        self._client.publish(topic, message)

    def _on_connection_successful(self):
        self._client.subscribe(f'{self.config.topic}/#')

    def _on_message(self, client, userdata, message):
        pass

    def _mqtt_topic_min(self):
        return len(self.config.topic.split('/') + 1)

    def __handle_all_message(self, topic_split, message):
        pass

    def __handle_driver_message(self, topic_split, message):
        pass

    def _run_event(self, event: Event):
        if event.data is None:
            return

        if event.event_type == EventType.MQTT_DEBUG:
            self.publish_debug_message(self.config.debug_topic, event.data)

        elif event.event_type == EventType.POINT_COV:
            self.publish_cov(event.data.get('source_driver'),
                             event.data.get('network').uuid, event.data.get('network').name,
                             event.data.get('device').uuid, event.data.get('device').name,
                             event.data.get('point'), event.data.get('point_store'),
                             )

        elif event.event_type == EventType.POINT_UPDATE or event.event_type == EventType.DEVICE_UPDATE or \
                event.event_type == EventType.NETWORK_UPDATE:
            self.publish_update(event.data.get('model'), event.data.get('updates'))

    def make_topic(self, part: tuple, sep: str = '/') -> str:
        wires_plat: dict = RubixRegistry().read_wires_plat()
        if not wires_plat:
            return ''
        return sep.join((wires_plat.get('client_id'), wires_plat.get('client_name'),
                         wires_plat.get('site_id'), wires_plat.get('site_name'),
                         wires_plat.get('device_id'), wires_plat.get('device_name')) + part)
