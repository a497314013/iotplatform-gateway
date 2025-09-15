

from iotplatform_gateway.connectors.converter import Converter, abstractmethod


class ModbusConverter(Converter):
    @abstractmethod
    def convert(self, config, data):
        pass
