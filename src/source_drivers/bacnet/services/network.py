import logging

import BAC0

from src.source_drivers.bacnet.models.network import BacnetNetworkModel
from src.utils import Singleton

logger = logging.getLogger(__name__)


class Network(metaclass=Singleton):

    def __init__(self):
        self.__networks = {}

    def start(self):
        logger.info("Network Start...")
        for network in BacnetNetworkModel.query.all():
            self.add_network(network)

    def add_network(self, network):
        net_url = f"{network.network_ip}/{network.network_mask}:{network.network_port}"
        network_device_id = network.network_device_id
        network_device_name = network.network_device_name

        if not self.__networks.get(net_url):
            self.__networks[net_url] = {}

        if not self.__networks.get(net_url).get(network_device_id):
            self.__networks[net_url][network_device_id] = {}

        logger.info('=====================================================')
        logger.info('...........Creating BACnet network with..............')
        logger.info(f'net_url: {net_url}')
        logger.info(f'network_device_id: {network_device_id}')
        logger.info(f'network_device_name: {network_device_name}')
        logger.info('.....................................................')
        logger.info('=====================================================')

        try:
            network = BAC0.lite(ip=net_url, deviceId=network_device_id, localObjName=network_device_name)
            self.__networks[net_url][network_device_id][network_device_name] = network
        except:
            logger.error("Initialization error!")

    def delete_network(self, network):
        net_url = f"{network.network_ip}/{network.network_mask}:{network.network_port}"
        network_device_id = network.network_device_id
        network_device_name = network.network_device_name

        network = self.__networks.get(net_url, {}).get(network_device_id, {}).get(network_device_name)
        if network:
            pass
            # TODO: uncomment, disconnect is not working fine
            # network.disconnect()
            # del self.networks[net_url][network_device_id][network_device_name]

    def get_network(self, network):
        net_url = f'{network.network_ip}/{network.network_mask}:{network.network_port}'
        network_device_id = network.network_device_id
        network_device_name = network.network_device_name
        return self.__networks.get(net_url, {}).get(network_device_id, {}).get(network_device_name)
