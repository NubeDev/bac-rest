import logging
import os

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()


def __db_setup(_app, _app_setting, db_pg: bool = False):
    if db_pg:
        _app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:postgres@localhost:5432/bac_rest"
        _app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_size': 10, 'max_overflow': 20}
    else:
        _app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}/data.db?timeout=60'.format(_app_setting.data_dir)
    _app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    _app.config['SQLALCHEMY_ECHO'] = False
    return _app


def create_app(app_setting) -> Flask:
    os.environ.setdefault('FLASK_ENV', 'production' if app_setting.prod else 'development')
    app = Flask(__name__)
    cors = CORS()
    app_setting = app_setting.init_app(app)
    app.config['CORS_HEADERS'] = 'Content-Type'
    cors.init_app(app)
    db.init_app(__db_setup(app, app_setting))

    def setup(self):
        gunicorn_logger = logging.getLogger('gunicorn.error')
        self.logger.handlers = gunicorn_logger.handlers
        self.logger.setLevel(gunicorn_logger.level)
        self.logger.info(self.config['SQLALCHEMY_DATABASE_URI'])

    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    def register_router(_app) -> Flask:
        from src.routes import bp_network, bp_device, bp_point, bp_generic, bp_modbus, bp_mapping_mp_gbp, bp_sync, \
            bp_system, bp_schedule, bp_setting
        _app.register_blueprint(bp_network)
        _app.register_blueprint(bp_device)
        _app.register_blueprint(bp_point)
        _app.register_blueprint(bp_generic)
        _app.register_blueprint(bp_modbus)
        _app.register_blueprint(bp_mapping_mp_gbp)
        _app.register_blueprint(bp_sync)
        _app.register_blueprint(bp_system)
        _app.register_blueprint(bp_schedule)
        _app.register_blueprint(bp_setting)
        return _app

    setup(app)
    return register_router(app)
