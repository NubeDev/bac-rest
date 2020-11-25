import logging.config
import os

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from src.event_dispatcher import EventDispatcher

logging.config.fileConfig('logging/logging.conf')

app = Flask(__name__)
CORS(app)

db_pg = False

if db_pg:
    app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:postgres@localhost:5432/bac_rest"
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'max_overflow': 20
    }
else:
    if os.environ.get("data_dir") is None:
        url = 'sqlite:///data.db?timeout=60'
    else:
        url = f'sqlite:///{os.environ.get("data_dir")}/data.db?timeout=60'

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', url)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False  # for print the sql query

db = SQLAlchemy(app)
from src import routes  # importing for creating all the schema on un-existing case
from src.models.point.model_point_store_history import PointStoreHistoryModel  # this one doesn't exist on routes

db.create_all()

with app.app_context():
    if os.environ.get("WERKZEUG_RUN_MAIN") or os.environ.get('SERVER_SOFTWARE'):
        from src.background import Background

        Background.run()
