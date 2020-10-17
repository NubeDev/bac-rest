from client import Client, Registers, Coils
import time
import logging

FORMAT = '%(asctime)-15s [%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT)
log = logging.getLogger("SDM630_READER")
log.setLevel(logging.INFO)

modbus = Client('config.json', 'rtu')

# CLASS
common_point_type = {
    "readCoils": "readCoils",
    "readDiscreteInputs": "readDiscreteInputs",
    "readHoldingRegisters": "readHoldingRegisters",
    "readInputRegisters": "readInputRegisters",
    "writeCoil": "writeCoil",
    "writeRegister": "writeRegister",
    "writeCoils": "writeCoils",
    "writeRegisters": "writeRegisters"
}


# def point_type(name: str) -> str:
def point_type(x: str):
    if common_point_type[x] == 'NY':
        return x
    return x


common_data_type = {
    "int16": "int16",
    "uint16": "uint16",
    "int32": "int32",
    "uint32": "uint32",
    "float": "float",
    "double": "double",
}

common_data_endian = {
    "LEB_BEW": "LEB_BEW",
    "LEB_LEW": "LEB_LEW",
    "BEB_LEW": "BEB_LEW",
    "BEB_BEW": "BEB_BEW"
}

common_point_enable = {
    "enable": "enable",
    "disable": "disable",
}

# will only send if new value over MQTT
common_only_send_on_cov = {
    "enable": "enable",
    "disable": "disable",
}

common_transport_method = {
    'TCP': 'tcp',
    'RTU': 'rtu',
}

common_registerDelay = 30

rtu_port = {
    "/dev/ttyUSB0": "/dev/ttyUSB0",
    "/dev/ttyUSB1": "/dev/ttyUSB1",
    "/dev/ttyUSB2": "/dev/ttyUSB2",
    "/dev/ttyUSB3": "/dev/ttyUSB3",
    "/dev/ttyUSB4": "/dev/ttyUSB4",
}

rtu_parity = {
    "even": "E",
    "odd": "O",
    "none": "N",
}

rtu_databits = {
    "even": "E",
    "odd": "O",
    "none": "N",
}

rtu_baud_rate = {
    "115200": 115200,
    "57600": 57600,
    "38400": 38400,
    "19200": 19200,
    "9600": 9600,
}

tcp_network = {
    "host": '0.0.0.0',
    "port": 502,
}

SLAVES = (1, 1)

RTU_NETWORK = {
    "NET_1": {
        "name": "name 111",
        "method": "rtu",
        "rs_port": "/dev/ttyUSB0",
        "speed": 9600,
        "stopbits": 1,
        "parity": "N",
        "bytesize": 8,  # 5, 6, 7, or 8. This defaults to 8.
        "timeout": 5,
        "global_device_timeout": 1,
        "global_point_timeout": 1,
    },
    "SLAVE_2": {
        "name": "name 111",
        "unit": 1,
        "timeout": 1,
        "ping_address": 1,
        "ping_point_type": common_point_type['readHoldingRegisters'],
    }
}

RTU_SLAVE = {
    "SLAVE_1": {
        "name": "name 111",
        "unit": 1,
        "timeout": 1,
        "ping_address": 1,
        "ping_point_type": common_point_type['readHoldingRegisters'],
        "ZeroMode": True
        # These are 0-based addresses. Therefore, the Modbus protocol address is equal to the Holding Register Offset minus one
    },
    "SLAVE_2": {
        "name": "name 111",
        "unit": 1,
        "timeout": 1,
        "ping_address": 1,
        "ping_point_type": common_point_type['readHoldingRegisters'],
    }
}

POINTS = {
    "PNT_1": {
        "name": "name 111",
        "point_type": point_type["readCoils"],
        "reg_start": 1,
        "reg_lenght": 2,
        "data_type": data_type["float"],
        "data_endian": data_endian["LEB_BEW"],
        "timeout": data_endian["LEB_BEW"]
    },
    "PNT_2": {
        "name": "name 332322",
        "point_type": point_type["readCoils"],
        "reg_start": 1,
        "reg_lenght": 2,
        "data_type": data_type["float"],
        "data_endian": data_endian["LEB_BEW"]
    }

}

client = modbus.make_client()
print(modbus.get_parm())
# reg = Registers(client, unit=1, reg_start=0, reg_lenght=2, data_type='float')
# bol = Coils(client, unit=1, reg_start=1, reg_lenght=10)

poll_count = 1


def print_data(ts, data):
    return print("{} : {}".format(ts, data), end=';\n')


try:
    while True:
        time.sleep(0.5)
        for slave in SLAVES:
            log.info("Handling slave=%s", slave)
            for key, point in POINTS.items():
                try:
                    # log.debug("Handling register=%s", reg_name)
                    # value = read_register(serial=serial, slave=slave, register=reg)
                    print('key', key)
                    print('point', point)
                    print('point', point["name"])
                    # regs = Registers(client, unit=slave, reg_start=reg, reg_lenght=2, data_type='float')
                    # holding = regs.read_holding()
                    # print('slave',slave, 'holding', holding)
                    # log.debug("Register=%s value read=%f", reg_name, reg)

                except:
                    log.error(
                        "Error handling register %s for slave=%s!", key, slave)
                    # traceback.print_exc()
    else:
        log.error("Cannot connect to serial device %s !", serial)

        print(2)
        # # reg.set_reg_adress(0)
        # # reg.set_lenght_data(nr)
        # # bol.set_lenght_data(nr)
        # try:
        #     holding = reg.read_holding()
        #     print(holding)
        #     # print_data(holding['Time'][1], holding['Data'])
        #     # time.sleep(0.1)
        #     # print("read next")
        #     # col = bol.read_coil()
        #     # print_data(col['Time'][1], col['Data'])
        #     # poll_count += 1
        #     # print("poll count" , poll_count)
        #     time.sleep(0.1)
        # except:
        #     print("An exception occurred")

except KeyboardInterrupt:
    print('\nEnd')
