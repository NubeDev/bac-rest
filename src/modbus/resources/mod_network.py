from flask_restful import Resource, reqparse, fields, marshal_with, abort
from src.modbus.models.mod_network import ModbusNetworkModel
from src.modbus.interfaces.network.interface_modbus_network import \
    interface_mod_network_name, interface_mod_network_type, \
    interface_mod_network_enable, interface_mod_network_timeout, \
    interface_mod_network_device_timeout_global, interface_mod_network_point_timeout_global, \
    interface_mod_rtu_network_port, interface_mod_rtu_network_speed, \
    interface_mod_rtu_network_stopbits, interface_mod_rtu_network_parity, \
    interface_mod_rtu_network_bytesize
from src.modbus.resources.mod_fields import network_fields


class ModNetwork(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument(interface_mod_network_name['name'],
                        type=interface_mod_network_name['type'],
                        required=interface_mod_network_name['required'],
                        help=interface_mod_network_name['help'],
                        )
    parser.add_argument(interface_mod_network_type['name'],
                        type=interface_mod_network_type['type'],
                        required=interface_mod_network_type['required'],
                        help=interface_mod_network_type['help'],
                        )
    parser.add_argument(interface_mod_network_enable['name'],
                        type=interface_mod_network_enable['type'],
                        required=interface_mod_network_enable['required'],
                        help=interface_mod_network_enable['help'],
                        )
    parser.add_argument(interface_mod_network_timeout['name'],
                        type=interface_mod_network_timeout['type'],
                        required=interface_mod_network_timeout['required'],
                        help=interface_mod_network_timeout['help'],
                        )
    parser.add_argument(interface_mod_network_device_timeout_global['name'],
                        type=interface_mod_network_device_timeout_global['type'],
                        required=interface_mod_network_device_timeout_global['required'],
                        help=interface_mod_network_device_timeout_global['help'],
                        )
    parser.add_argument(interface_mod_network_point_timeout_global['name'],
                        type=interface_mod_network_point_timeout_global['type'],
                        required=interface_mod_network_point_timeout_global['required'],
                        help=interface_mod_network_point_timeout_global['help'],
                        )
    parser.add_argument(interface_mod_rtu_network_port['name'],
                        type=interface_mod_rtu_network_port['type'],
                        required=interface_mod_rtu_network_port['required'],
                        help=interface_mod_rtu_network_port['help'],
                        )
    parser.add_argument(interface_mod_rtu_network_speed['name'],
                        type=interface_mod_rtu_network_speed['type'],
                        required=interface_mod_rtu_network_speed['required'],
                        help=interface_mod_rtu_network_speed['help'],
                        )
    parser.add_argument(interface_mod_rtu_network_stopbits['name'],
                        type=interface_mod_rtu_network_stopbits['type'],
                        required=interface_mod_rtu_network_stopbits['required'],
                        help=interface_mod_rtu_network_stopbits['help'],
                        )
    parser.add_argument(interface_mod_rtu_network_parity['name'],
                        type=interface_mod_rtu_network_parity['type'],
                        required=interface_mod_rtu_network_parity['required'],
                        help=interface_mod_rtu_network_parity['help'],
                        )
    parser.add_argument(interface_mod_rtu_network_bytesize['name'],
                        type=interface_mod_rtu_network_bytesize['type'],
                        required=interface_mod_rtu_network_bytesize['required'],
                        help=interface_mod_rtu_network_bytesize['help'],
                        )

    @marshal_with(network_fields)
    def get(self, uuid):
        network = ModbusNetworkModel.find_by_network_uuid(uuid)
        if not network:
            abort(404, message='Modbus Network not found')
        return network

    @marshal_with(network_fields)
    def post(self, uuid):
        if ModbusNetworkModel.find_by_network_uuid(uuid):
            return abort(409, message=f"An Modbus Network with network_uuid '{uuid}' already exists.")
        data = ModNetwork.parser.parse_args()
        try:
            network = ModNetwork.create_network_model_obj(uuid, data)
            network.save_to_db()
            return network, 201
        except Exception as e:
            return abort(500, message=str(e))

    @marshal_with(network_fields)
    def put(self, uuid):
        data = ModNetwork.parser.parse_args()
        network = ModbusNetworkModel.find_by_network_uuid(uuid)
        if network is None:
            try:
                network = ModNetwork.create_network_model_obj(uuid, data)
            except Exception as e:
                return abort(500, message=str(e))
        else:
            network.mod_network_name = data['mod_network_name']
            network.mod_network_type = data['mod_network_type']
            network.mod_network_port = data['mod_network_enable']
            network.mod_network_port = data['mod_network_timeout']
            network.mod_network_port = data['mod_network_device_timeout_global']
            network.mod_network_port = data['mod_network_point_timeout_global']
            network.mod_network_port = data['mod_rtu_network_port']
            network.mod_network_port = data['mod_rtu_network_speed']
            network.mod_network_port = data['mod_rtu_network_stopbits']
            network.mod_network_port = data['mod_rtu_network_parity']
            network.mod_network_port = data['mod_rtu_network_bytesize']
        network.save_to_db()
        return network, 201

    def delete(self, uuid):
        mod_network_uuid = uuid
        network = ModbusNetworkModel.find_by_network_uuid(mod_network_uuid)
        if network:
            network.delete_from_db()
        return '', 204

    @staticmethod
    def create_network_model_obj(mod_network_uuid, data):
        return ModbusNetworkModel(mod_network_uuid=mod_network_uuid,
                                  mod_network_name=data['mod_network_name'],
                                  mod_network_type=data['mod_network_type'],
                                  mod_network_enable=data['mod_network_enable'],
                                  mod_network_timeout=data['mod_network_timeout'],
                                  mod_network_device_timeout_global=data['mod_network_device_timeout_global'],
                                  mod_network_point_timeout_global=data['mod_network_point_timeout_global'],
                                  mod_rtu_network_port=data['mod_rtu_network_port'],
                                  mod_rtu_network_speed=data['mod_rtu_network_speed'],
                                  mod_rtu_network_stopbits=data['mod_rtu_network_stopbits'],
                                  mod_rtu_network_parity=data['mod_rtu_network_parity'],
                                  mod_rtu_network_bytesize=data['mod_rtu_network_bytesize'])


class ModNetworkList(Resource):
    @marshal_with(network_fields, envelope="mod_networks")
    def get(self):
        return ModbusNetworkModel.query.all()


class ModNetworksIds(Resource):
    @marshal_with({'mod_network_uuid': fields.String}, envelope="mod_networks")
    def get(self):
        return ModbusNetworkModel.query.all()
