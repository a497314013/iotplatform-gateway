

from iotplatform_gateway.connectors.converter import Converter, abstractmethod


class OcppConverter(Converter):
    @abstractmethod
    def convert(self, config, data):
        pass
