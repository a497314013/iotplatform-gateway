

from iotplatform_gateway.connectors.converter import Converter, abstractmethod


class KNXConverter(Converter):
    @abstractmethod
    def convert(self, data):
        pass
