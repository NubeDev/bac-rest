from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

from src.modbus.interfaces.point.points import ModbusPointUtilsFuncs, ModbusPointUtils
from src.modbus.services.modbus_functions.debug import modbus_debug_funcs


def read_holding(client, reg_start, reg_length, _unit, data_type, endian):
    """
    read holding register
    :return:holding reg
    """
    # debug
    if modbus_debug_funcs:
        print("MODBUS read_holding, check reg_length")
    reg_type = 'holding'
    # check that user if for example wants data type of float that the reg_length is > = 2
    reg_length = _set_data_length(data_type, reg_length)
    # debug
    if modbus_debug_funcs:
        print("MODBUS read_holding, check reg_length result then do modbus read", "reg_length", reg_length)
    read = client.read_holding_registers(reg_start, reg_length, unit=_unit)
    # debug
    if modbus_debug_funcs:
        print("MODBUS read_holding, do modbus read", read)
    if not _assertion(read, client, reg_type):  # checking for errors
        bo_wo = _mod_point_data_endian(endian)
        byteorder = bo_wo['bo']
        wordorder = bo_wo['wo']
        data_type = _select_data_type(read, data_type, byteorder, wordorder)
        val = data_type
        return {'val': val, 'array': read.registers}


def _set_data_length(data_type, reg_length):
    """
    Sets the data length for the selected data type
    :return:holding reg
    """
    if modbus_debug_funcs: print("MODBUS: in function  _set_data_length, check reg_length", data_type, reg_length)
    _val = data_type
    length = reg_length

    if True:  # TODO add a check for data type
        _type = ModbusPointUtils.mod_point_data_type
        _int16 = _type['int16']
        _uint16 = _type['uint16']
        _int32 = _type['int16']
        _uint32 = _type['uint32']
        _float = _type['float']
        _double = _type['double']
        if _val == _int16 or _val == _uint16:
            if reg_length < 1:
                return 1
            else:
                return length
        if _val == _int32 or _val == _uint32 or _val == _float:
            if reg_length < 2:
                return 2
            else:
                return length
        elif _val == _double:
            if reg_length < 4:
                return 4
            else:
                return length


def _mod_point_data_endian(_val: str):
    """
    Sets byte order and endian order
    :return: array {'bo': bo, 'wo': wo}
    """
    if ModbusPointUtilsFuncs.func_common_data_endian(_val):
        if _val == ModbusPointUtils.mod_point_data_endian['LEB_BEW']:
            bo = Endian.Little
            wo = Endian.Big
            return {'bo': bo, 'wo': wo}
        if _val == ModbusPointUtils.mod_point_data_endian['LEB_LEW']:
            bo = Endian.Little
            wo = Endian.Little
            return {'bo': bo, 'wo': wo}
        if _val == ModbusPointUtils.mod_point_data_endian['BEB_LEW']:
            bo = Endian.Big
            wo = Endian.Little
            return {'bo': bo, 'wo': wo}
        if _val == ModbusPointUtils.mod_point_data_endian['BEB_BEW']:
            bo = Endian.Big
            wo = Endian.Big
            return {'bo': bo, 'wo': wo}


def _assertion(operation, client, reg_type):
    """
    :param operation: Client method. Checks whether data has been downloaded
    :return: Status False to OK or True.
    """
    # test that we are not an error
    if not operation.isError():
        pass
    else:
        print("connects to port: {}; Type Register: {}; Exception: {}".format(client.port,
                                                                              reg_type,
                                                                              operation, ))
    return operation.isError()


def _select_data_type(data, data_type, byteorder, wordorder):
    """
    Converts the data type int, int32, float and so on
    :param data: Log List Downloaded
    :return: data in the selected data type
    """
    decoder = BinaryPayloadDecoder.fromRegisters(data.registers, byteorder=byteorder,
                                                 wordorder=wordorder)
    if data_type == 'int16':
        data = decoder.decode_16bit_int()
    if data_type == 'uint16':
        data = decoder.decode_16bit_uint()
    if data_type == 'int32':
        data = decoder.decode_32bit_int()
    if data_type == 'uint32':
        data = decoder.decode_32bit_uint()
    if data_type == 'float':
        data = decoder.decode_32bit_float()
    elif data_type == 'double':
        data = decoder.decode_32bit_float()
    return data
