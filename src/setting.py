import os
from configparser import ConfigParser
from typing import List

from flask import Flask


class BaseSetting:

    def reload(self, setting: dict):
        if setting is not None:
            self.__dict__ = {k: setting.get(k, v) for k, v in self.__dict__.items()}
        return self


class ServiceSetting(BaseSetting):
    """
    Declares an availability service(enabled/disabled option)
    """

    KEY = 'services'

    def __init__(self):
        self.mqtt = True
        self.histories = True
        self.cleaner = True
        self.history_sync = True


class DriverSetting(BaseSetting):
    """
    Declares an availability driver(enabled/disabled option)
    """

    KEY = 'drivers'

    def __init__(self):
        self.generic: bool = True
        self.modbus_rtu: bool = True
        self.modbus_tcp: bool = True


class MqttSetting(BaseSetting):
    KEY = 'mqtt'

    def __init__(self):
        self.enabled = True
        self.name = 'rubix_points'
        self.host = '0.0.0.0'
        self.port = 1883
        self.keepalive = 60
        self.qos = 1
        self.retain = False
        self.attempt_reconnect_on_unavailable = True
        self.attempt_reconnect_secs = 5
        self.publish_value = True
        self.topic = 'rubix/points'


class GenericListenerSetting(MqttSetting):
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

    def __init__(self, **kwargs):
        self.__data_dir = self.__compute_dir(kwargs.get('data_dir'), AppSetting.default_data_dir)
        self.__prod = kwargs.get('prod') or False
        self.__service_setting = ServiceSetting()
        self.__driver_setting = DriverSetting()
        self.__influx_setting = InfluxSetting()
        self.__listener_setting = GenericListenerSetting()
        self.__mqtt_settings: List[MqttSetting] = []

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

    def reload(self, setting_file: str, logging_file: str):
        parser = self.__read_file(setting_file, self.__data_dir)
        return self._reload(parser)

    def _reload(self, parser):
        self.__driver_setting = self.__driver_setting.reload(self.__load(parser, DriverSetting.KEY))
        self.__service_setting = self.__service_setting.reload(self.__load(parser, ServiceSetting.KEY))
        self.__influx_setting = self.__influx_setting.reload(self.__load(parser, InfluxSetting.KEY))
        self.__listener_setting = self.__listener_setting.reload(self.__load(parser, GenericListenerSetting.KEY))
        self.__mqtt_settings = self.__load_mqtt(parser, MqttSetting.KEY)
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
    def __read_file(setting_file: str, _dir: str):
        if setting_file is None or setting_file.strip() == '':
            return None
        s = setting_file if os.path.isabs(setting_file) else os.path.join(_dir, setting_file)
        if not os.path.isfile(s) or not os.path.exists(s):
            return None
        parser = ConfigParser()
        parser.read(setting_file)
        return parser

    @staticmethod
    def __load(parser: ConfigParser, section: str) -> dict:
        if parser is None:
            return {}
        return dict(parser.items(section)) if parser.has_section(section) else None

    @staticmethod
    def __load_mqtt(parser: ConfigParser, prefix: str) -> List[MqttSetting]:
        if parser is None:
            return []
        return [MqttSetting().reload(AppSetting.__load(parser, s)) for s in parser.sections() if s.startswith(prefix)]
