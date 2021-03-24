import uuid as uuid_
import logging

from src import db, InfluxSetting
from src.models.setting.model_setting_base import SettingBaseModel

logger = logging.getLogger(__name__)


class InfluxSettingModel(SettingBaseModel):
    __tablename__ = 'influx_settings'
    uuid = db.Column(db.String(80), primary_key=True, nullable=False)
    host = db.Column(db.String(80), nullable=False)
    port = db.Column(db.Integer(), nullable=False)
    database = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    ssl = db.Column(db.Boolean(), nullable=False)
    verify_ssl = db.Column(db.Boolean(), nullable=False)
    timeout = db.Column(db.Integer(), nullable=False)
    retries = db.Column(db.Integer(), nullable=False)
    timer = db.Column(db.Integer(), nullable=False)
    path = db.Column(db.String(80), nullable=False)
    measurement = db.Column(db.String(80), nullable=False)
    attempt_reconnect_secs = db.Column(db.Integer(), nullable=False)

    def __repr__(self):
        return f"InfluxSetting(uuid = {self.uuid})"

    @classmethod
    def create_default_if_does_not_exists(cls, config: InfluxSetting):
        influx_setting = cls.find_one()
        if not influx_setting:
            uuid = str(uuid_.uuid4())
            influx_setting = InfluxSettingModel(uuid=uuid,
                                                host=config.host,
                                                port=config.port,
                                                database=config.database,
                                                username=config.username,
                                                password=config.password,
                                                ssl=config.ssl,
                                                verify_ssl=config.verify_ssl,
                                                timeout=config.timeout,
                                                retries=config.retries,
                                                timer=config.timer,
                                                path=config.path,
                                                measurement=config.measurement,
                                                attempt_reconnect_secs=config.attempt_reconnect_secs)
            influx_setting.save_to_db()
        return influx_setting
