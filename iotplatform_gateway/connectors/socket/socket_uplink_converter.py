

from iotplatform_gateway.connectors.converter import Converter, abstractmethod


class SocketUplinkConverter(Converter):

    @abstractmethod
    def convert(self, config, data):
        pass
