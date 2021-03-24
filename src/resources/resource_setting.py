from flask_restful import reqparse, marshal_with
from rubix_http.exceptions.exception import NotFoundException
from rubix_http.resource import RubixResource

from src.models.setting.model_setting_influx import InfluxSettingModel
from src.models.setting.model_setting_postgres import PostgresSettingModel
from src.resources.rest_schema.schema_setting import influx_setting_all_attributes, influx_setting_return_attributes, \
    postgres_setting_all_attributes, postgres_setting_return_attributes
from src.services.histories.sync.influxdb import InfluxDB
from src.services.histories.sync.postgresql import PostgreSQL


class InfluxSettingResource(RubixResource):
    patch_parser = reqparse.RequestParser()
    for attr in influx_setting_all_attributes:
        patch_parser.add_argument(attr,
                                  type=influx_setting_all_attributes[attr]['type'],
                                  required=False,
                                  store_missing=False)

    @classmethod
    @marshal_with(influx_setting_return_attributes)
    def get(cls):
        return InfluxSettingModel.find_one()

    @classmethod
    @marshal_with(influx_setting_return_attributes)
    def patch(cls):
        data = cls.patch_parser.parse_args()
        influx_setting = InfluxSettingModel.find_one()
        if not influx_setting:
            raise NotFoundException('Influx setting not found')
        if influx_setting.update(**data):
            InfluxDB().restart_influx(influx_setting)
        return influx_setting


class PostgresSettingResource(RubixResource):
    patch_parser = reqparse.RequestParser()
    for attr in postgres_setting_all_attributes:
        patch_parser.add_argument(attr,
                                  type=postgres_setting_all_attributes[attr]['type'],
                                  required=False,
                                  store_missing=False)

    @classmethod
    @marshal_with(postgres_setting_return_attributes)
    def get(cls):
        postgres_setting = PostgresSettingModel.find_one()
        return postgres_setting

    @classmethod
    @marshal_with(postgres_setting_return_attributes)
    def patch(cls):
        data = cls.patch_parser.parse_args()
        postgres_setting = PostgresSettingModel.find_one()
        if not postgres_setting:
            raise NotFoundException('Postgres setting not found')
        if postgres_setting.update(**data):
            PostgreSQL().restart_postgres(postgres_setting)
        return postgres_setting
