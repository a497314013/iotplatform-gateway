

from iotplatform_gateway.connectors.converter import Converter, abstractmethod


class BLEUplinkConverter(Converter):

    @abstractmethod
    def convert(self, config, data):
        pass
