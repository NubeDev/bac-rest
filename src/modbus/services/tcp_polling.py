import time
from src.modbus.interfaces.point.points import ModbusFC
from src import db
from src.modbus.models.mod_device import ModbusDeviceModel
from src.modbus.models.mod_network import ModbusNetworkModel, ModbusType
from src.modbus.models.mod_point import ModbusPointModel
from src.modbus.models.mod_point_store import ModbusPointStoreModel
from src.modbus.services.tcp_registry import TcpRegistry
from src.utils.data_funcs import DataHelpers


class TcpPolling:
    _instance = None
    _polling_period = 2

    @staticmethod
    def get_instance():
        if not TcpPolling._instance:
            TcpPolling()
        return TcpPolling._instance

    def __init__(self):
        if TcpPolling._instance:
            raise Exception("TcpPolling class is a singleton class!")
        else:
            TcpPolling._instance = self

    def polling(self):
        print("TCP Polling started")
        count = 0
        while True:
            time.sleep(2)
            count += 1
            print(f'Looping {count}...')
            results = db.session.query(ModbusNetworkModel, ModbusDeviceModel, ModbusPointModel). \
                select_from(ModbusNetworkModel).filter_by(mod_network_type=ModbusType.TCP).join(
                ModbusDeviceModel).filter_by(mod_device_type=ModbusType.TCP).join(
                ModbusPointModel).all()
            for network, device, point in results:
                self.poll_point(device, point)

    def poll_point(self, device, point):
        host = device.mod_tcp_device_ip
        port = device.mod_tcp_device_port
        mod_device_addr = device.mod_device_addr
        mod_point_reg_length = point.mod_point_reg_length
        mod_point_type = point.mod_point_type
        tcp_connection = TcpRegistry.get_tcp_connections().get(TcpRegistry.create_connection_key(host, port))
        if not tcp_connection:
            TcpRegistry.get_instance().add_device(device)
        # TODO: confirm whether this column is correct or not
        reg = point.mod_point_reg
        # TODO: Manually put 1 for now
        # unit = 1
        try:
            val = None
            if mod_point_type == ModbusFC.readCoils:
                val = tcp_connection.read_coils(reg, mod_point_reg_length, unit=mod_device_addr)
                val = val.registers[0]
                val = DataHelpers.bool_to_int(val)
            if mod_point_type == ModbusFC.readHoldingRegisters:
                val = tcp_connection.read_holding_registers(reg, mod_point_reg_length, unit=mod_device_addr)
                val = val.registers[0]
            if val:
                print('val:', val, 'reg:', reg)
                ModbusPointStoreModel(mod_point_value=val, mod_point_uuid=point.mod_point_uuid).save_to_db()
        except Exception as e:
            print(str(e))
