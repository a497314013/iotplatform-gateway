

from iotplatform_gateway.connectors.converter import Converter, abstractmethod


class RequestUplinkConverter(Converter):

    @abstractmethod
    def convert(self, config, data):
        pass
