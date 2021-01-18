import json
import os
from typing import List

from flask import Flask


class BaseSetting:

    def reload(self, setting: dict):
        if setting is not None:
            self.__dict__ = {k: setting.get(k, v) for k, v in self.__dict__.items()}
        return self

    def serialize(self, pretty=True) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, indent=2 if pretty else None)

    def to_dict(self):
        return json.loads(self.serialize(pretty=False))


class ServiceSetting(BaseSetting):
    """
    Declares an availability service(enabled/disabled option)
    """

    KEY = 'services'

    def __init__(self):
        self.mqtt = True
        self.histories = False
        self.cleaner = False
        self.history_sync = False


class DriverSetting(BaseSetting):
    """
    Declares an availability driver(enabled/disabled option)
    """

    KEY = 'drivers'

    def __init__(self):
        self.generic: bool = False
        self.modbus_rtu: bool = True
        self.modbus_tcp: bool = False


class MqttSettingBase(BaseSetting):
    def __init__(self):
        self.enabled = True
        self.name = ''
        self.host = '0.0.0.0'
        self.port = 1883
        self.keepalive = 60
        self.qos = 1
        self.retain = False
        self.attempt_reconnect_on_unavailable = True
        self.attempt_reconnect_secs = 5
        self.publish_value = True
        self.topic = ''


class MqttSetting(MqttSettingBase):
    KEY = 'mqtt'

    def __init__(self):
        super(MqttSetting, self).__init__()
        self.name = 'rubix_points'
        self.topic = 'rubix/points/value'
        self.publish_debug = True
        self.debug_topic = 'rubix/points/debug'


class GenericListenerSetting(MqttSettingBase):
    KEY = 'generic_point_listener'

    def __init__(self):
        super(GenericListenerSetting, self).__init__()
        self.name = 'rubix_points_generic_point'
        self.topic = 'rubix/points/generic/cov'


class InfluxSetting(BaseSetting):
    KEY = 'influx'

    def __init__(self):
        self.host = '0.0.0.0'
        self.port = 8086
        self.database = 'db'
        self.username = 'username'
        self.password = 'password'
        self.verify_ssl = False
        self.timeout = 5
        self.retries = 3
        self.timer = 1
        self.path = ''
        self.measurement = 'history'


class AppSetting:
    DATA_DIR_ENV = 'RUBIX_POINT_DATA'
    KEY: str = 'APP_SETTING'
    default_data_dir: str = 'out'
    default_setting_file: str = 'config.json'
    default_logging_conf: str = 'logging.conf'
    fallback_logging_conf: str = 'config/logging.example.conf'
    fallback_prod_logging_conf: str = 'config/logging.prod.example.conf'

    def __init__(self, **kwargs):
        self.__data_dir = self.__compute_dir(kwargs.get('data_dir'), AppSetting.default_data_dir)
        self.__prod = kwargs.get('prod') or False
        self.__service_setting = ServiceSetting()
        self.__driver_setting = DriverSetting()
        self.__influx_setting = InfluxSetting()
        self.__listener_setting = GenericListenerSetting()
        self.__mqtt_settings: List[MqttSetting] = [MqttSetting()]

    @property
    def data_dir(self):
        return self.__data_dir

    @property
    def prod(self) -> bool:
        return self.__prod

    @property
    def services(self) -> ServiceSetting:
        return self.__service_setting

    @property
    def drivers(self) -> DriverSetting:
        return self.__driver_setting

    @property
    def influx(self) -> InfluxSetting:
        return self.__influx_setting

    @property
    def mqtt_settings(self) -> List[MqttSetting]:
        return self.__mqtt_settings

    @property
    def listener(self) -> GenericListenerSetting:
        return self.__listener_setting

    def serialize(self, pretty=True) -> str:
        m = {
            DriverSetting.KEY: self.drivers,
            ServiceSetting.KEY: self.services,
            InfluxSetting.KEY: self.influx,
            GenericListenerSetting.KEY: self.listener,
            MqttSetting.KEY: [s.to_dict() for s in self.mqtt_settings],
            'prod': self.prod, 'data_dir': self.data_dir
        }
        return json.dumps(m, default=lambda o: o.to_dict() if isinstance(o, BaseSetting) else o.__dict__,
                          indent=2 if pretty else None)

    def reload(self, setting_file: str, is_json_str: bool = False):
        data = self.__read_file(setting_file, self.__data_dir, is_json_str)
        self.__driver_setting = self.__driver_setting.reload(data.get(DriverSetting.KEY))
        self.__service_setting = self.__service_setting.reload(data.get(ServiceSetting.KEY))
        self.__influx_setting = self.__influx_setting.reload(data.get(InfluxSetting.KEY))
        self.__listener_setting = self.__listener_setting.reload(data.get(GenericListenerSetting.KEY))
        mqtt_settings = data.get(MqttSetting.KEY, [])
        if len(mqtt_settings) > 0:
            self.__mqtt_settings = [MqttSetting().reload(s) for s in mqtt_settings]
        return self

    def init_app(self, app: Flask):
        app.config[AppSetting.KEY] = self
        return self

    @staticmethod
    def __compute_dir(_dir: str, _def: str, mode=0o744) -> str:
        d = os.path.join(os.getcwd(), _def) if _dir is None or _dir.strip() == '' else _dir
        d = d if os.path.isabs(d) else os.path.join(os.getcwd(), d)
        os.makedirs(d, mode, True)
        return d

    @staticmethod
    def __read_file(setting_file: str, _dir: str, is_json_str=False):
        if is_json_str:
            return json.loads(setting_file)
        if setting_file is None or setting_file.strip() == '':
            return {}
        s = setting_file if os.path.isabs(setting_file) else os.path.join(_dir, setting_file)
        if not os.path.isfile(s) or not os.path.exists(s):
            return {}
        with open(s) as json_file:
            return json.load(json_file)
