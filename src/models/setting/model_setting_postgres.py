import uuid as uuid_
import logging

from src import db, PostgresSetting
from src.models.setting.model_setting_base import SettingBaseModel

logger = logging.getLogger(__name__)


class PostgresSettingModel(SettingBaseModel):
    __tablename__ = 'postgres_settings'
    uuid = db.Column(db.String(80), primary_key=True, nullable=False)
    host = db.Column(db.String(80), nullable=False)
    port = db.Column(db.Integer(), nullable=False)
    dbname = db.Column(db.String(80), nullable=False)
    user = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    ssl_mode = db.Column(db.String(80), nullable=False)
    connect_timeout = db.Column(db.Integer(), nullable=False)
    timer = db.Column(db.Integer(), nullable=False)
    table_name = db.Column(db.String(80), nullable=False)
    attempt_reconnect_secs = db.Column(db.Integer(), nullable=False)

    def __repr__(self):
        return f"PostgresSetting(uuid = {self.uuid})"

    @classmethod
    def create_default_if_does_not_exists(cls, config: PostgresSetting):
        postgres_setting = cls.find_one()
        if not postgres_setting:
            uuid = str(uuid_.uuid4())
            postgres_setting = PostgresSettingModel(uuid=uuid,
                                                    host=config.host,
                                                    port=config.port,
                                                    dbname=config.dbname,
                                                    user=config.user,
                                                    password=config.password,
                                                    ssl_mode=config.ssl_mode,
                                                    connect_timeout=config.connect_timeout,
                                                    timer=config.timer,
                                                    table_name=config.table_name,
                                                    attempt_reconnect_secs=config.attempt_reconnect_secs)
            postgres_setting.save_to_db()
        return postgres_setting
