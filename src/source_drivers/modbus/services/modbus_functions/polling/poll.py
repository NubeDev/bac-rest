import numbers

from src import TcpRegistry, PointStoreHistoryModel
from src.interfaces.point import HistoryType
from src.models.point.model_point_store import PointStoreModel
from src.source_drivers.modbus.interfaces.network.network import ModbusType
from src.source_drivers.modbus.interfaces.point.points import ModbusPointType
from src.source_drivers.modbus.services.modbus_functions.debug import modbus_debug_poll
from src.source_drivers.modbus.services.modbus_functions.polling.poll_funcs import read_input_registers_handle, \
    read_holding_registers_handle, \
    write_coil_handle, \
    read_coils_handle, write_registers_handle
from src.source_drivers.modbus.services.rtu_registry import RtuRegistry
from src.utils.model_utils import ModelUtils


def poll_point(network, device, point, transport) -> None:
    """
    Main modbus polling loop
    :param network: modbus network class
    :param device: modbus device class
    :param point: modbus point class
    :param transport: modbus transport as in TCP or RTU
    :return: None
    """

    """
    DEBUG
    """
    if modbus_debug_poll:
        print('MODBUS DEBUG: main looping function poll_point')
    connection = None
    if transport == ModbusType.RTU:
        connection = RtuRegistry.get_rtu_connections().get(RtuRegistry.create_connection_key_by_network(network))
        if not connection:
            RtuRegistry.get_instance().add_network(network)
    if transport == ModbusType.TCP:
        host = device.tcp_ip
        port = device.tcp_port
        connection = TcpRegistry.get_tcp_connections().get(TcpRegistry.create_connection_key(host, port))
        if not connection:
            TcpRegistry.get_instance().add_device(device)

    mod_device_address = device.address
    reg = point.reg
    mod_point_reg_length = point.reg_length
    mod_point_type = point.type
    mod_point_data_type = point.data_type
    mod_point_data_endian = point.data_endian

    write_value = point.write_value
    read_coils = ModbusPointType.READ_COILS
    write_coil = ModbusPointType.WRITE_COIL
    read_holding_registers = ModbusPointType.READ_HOLDING_REGISTERS
    read_input_registers = ModbusPointType.READ_DISCRETE_INPUTS
    write_registers = ModbusPointType.WRITE_REGISTERS
    """
    DEBUG
    """
    if modbus_debug_poll:
        print("@@@ START MODBUS POLL !!!")
        print("MODBUS DEBUG:", {'network': network,
                                'device': device,
                                'transport': transport,
                                'mod_device_address': mod_device_address,
                                'reg': reg,
                                'mod_point_reg_length': mod_point_reg_length,
                                'mod_point_type': mod_point_type,
                                'mod_point_data_type': mod_point_data_type,
                                'mod_point_data_endian': mod_point_data_endian,
                                'write_value': write_value
                                })

    fault = False
    fault_message = ""
    point_store_new = None
    try:
        val = None
        array = ""
        """
        read_coils
        """
        if mod_point_type == read_coils:
            val, array = read_coils_handle(connection,
                                           reg,
                                           mod_point_reg_length,
                                           mod_device_address,
                                           mod_point_type)
        """
        write_coils
        """
        if mod_point_type == write_coil:
            val, array = write_coil_handle(connection, reg,
                                           mod_point_reg_length,
                                           mod_device_address,
                                           write_value,
                                           mod_point_type)
        """
        read_input_registers
        """
        if mod_point_type == read_input_registers:
            val, array = read_input_registers_handle(connection,
                                                     reg,
                                                     mod_point_reg_length,
                                                     mod_device_address,
                                                     mod_point_data_type,
                                                     mod_point_data_endian,
                                                     mod_point_type)
        """
        read_holding_registers
        """
        if mod_point_type == read_holding_registers:
            val, array = read_holding_registers_handle(connection,
                                                       reg,
                                                       mod_point_reg_length,
                                                       mod_device_address,
                                                       mod_point_data_type,
                                                       mod_point_data_endian,
                                                       mod_point_type)
        """
        write_registers write_registers
        """
        if mod_point_type == write_registers:
            val, array = write_registers_handle(connection,
                                                reg,
                                                mod_point_reg_length,
                                                mod_device_address,
                                                mod_point_data_type,
                                                mod_point_data_endian,
                                                write_value,
                                                mod_point_type)

        """
        Save modbus data in database
        """
        if modbus_debug_poll:
            print("MODBUS DEBUG: READ/WRITE WAS DONE", 'TRANSPORT TYPE & VAL', {"transport": transport, "val": val})
        if isinstance(val, numbers.Number):
            point_store_new = PointStoreModel(value=val, value_array=str(array), point_uuid=point.uuid)
        else:
            fault = True
            fault_message = "Got non numeric value"
    except Exception as e:
        if modbus_debug_poll:
            print(f'MODBUS ERROR: in poll main function {str(e)}')
        fault = True
        fault_message = str(e)
    if not point_store_new:
        point_store_new = PointStoreModel(value=0, fault=fault, fault_message=fault_message, point_uuid=point.uuid)
    if modbus_debug_poll:
        print("!!! END MODBUS POLL @@@")

    update_point_store(network, device, point, point_store_new)


def update_point_store(network, device, point, point_store_new):
    """
    It compares :param {PointStoreModel} point_store_new with the existing point_store value for that particular point &
    If new: update it
    If old: do nothing
    """
    point_store_existing = PointStoreModel.find_by_point_uuid(point.uuid)

    if not point_store_existing:
        # If some manual point_store table deletion occurred
        point_store_existing = PointStoreModel.create_new_point_store_model(point.uuid)
        point_store_existing.save_to_db()

    _point_store_existing = ModelUtils.row2dict_default(point_store_existing)
    del _point_store_existing['ts']

    _point_store_new = ModelUtils.row2dict_default(point_store_new)
    del _point_store_new['ts']

    if _point_store_new != _point_store_existing:
        point_store_existing.update(**_point_store_new)
        add_point_history_on_cov(network, device, point)


def add_point_history_on_cov(network, device, point):
    """
    add point.point_store to the point_store_history if they history type is 'COV' and history_enable is `True`
    """
    if point.history_type == HistoryType.COV \
            and network.history_enable and device.history_enable and point.history_enable:
        data = ModelUtils.row2dict_default(PointStoreModel.find_by_point_uuid(point.uuid))
        point_store_history = PointStoreHistoryModel(**data)
        point_store_history.save_to_db()
