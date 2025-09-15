

from iotplatform_gateway.connectors.converter import Converter, abstractmethod


class FTPConverter(Converter):
    @abstractmethod
    def convert(self, config, data):
        pass
