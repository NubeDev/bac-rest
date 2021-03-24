from flask_restful import fields

from src.resources.utils import map_rest_schema

# Mqtt
influx_setting_all_attributes = {
    'uuid': {
        'type': str,
    },
    'host': {
        'type': str,
        'required': True,
    },
    'port': {
        'type': int,
        'required': True,
    },
    'database': {
        'type': str,
        'required': True,
    },
    'username': {
        'type': str,
        'required': True,
    },
    'password': {
        'type': str,
        'required': True,
    },
    'ssl': {
        'type': bool,
        'required': True,
    },
    'verify_ssl': {
        'type': bool,
        'required': True,
    },
    'timeout': {
        'type': int,
        'required': True,
    },
    'retries': {
        'type': int,
        'required': True,
    },
    'timer': {
        'type': int,
        'required': True,
    },
    'path': {
        'type': str,
        'required': True,
    },
    'measurement': {
        'type': str,
        'required': True,
    },
    'attempt_reconnect_secs': {
        'type': int,
        'required': True,
    },
}

influx_setting_return_attributes = {
    'uuid': fields.String,
    'host': fields.String,
    'port': fields.Integer,
    'database': fields.String,
    'username': fields.String,
    'ssl': fields.Boolean,
    'verify_ssl': fields.Boolean,
    'timeout': fields.Integer,
    'retries': fields.Integer,
    'timer': fields.Integer,
    'path': fields.String,
    'measurement': fields.String,
    'attempt_reconnect_secs': fields.Integer,
}

# Postgres
postgres_setting_all_attributes = {
    'uuid': {
        'type': str,
    },
    'host': {
        'type': str,
        'required': True,
    },
    'port': {
        'type': int,
        'required': True,
    },
    'dbname': {
        'type': str,
        'required': True,
    },
    'user': {
        'type': str,
        'required': True,
    },
    'password': {
        'type': str,
        'required': True,
    },
    'ssl_mode': {
        'type': str,
        'required': True,
    },
    'connect_timeout': {
        'type': int,
        'required': True,
    },
    'timer': {
        'type': int,
        'required': True,
    },
    'table_name': {
        'type': str,
        'required': True,
    },
    'attempt_reconnect_secs': {
        'type': int,
        'required': True,
    }
}

postgres_setting_return_attributes = {
    'uuid': fields.String,
    'host': fields.String,
    'port': fields.Integer,
    'dbname': fields.String,
    'user': fields.String,
    'ssl_mode': fields.String,
    'connect_timeout': fields.Integer,
    'timer': fields.Integer,
    'table_name': fields.String,
    'attempt_reconnect_secs': fields.Integer
}
