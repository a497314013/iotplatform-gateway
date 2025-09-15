

from iotplatform_gateway.connectors.converter import Converter, abstractmethod


class XmppConverter(Converter):
    @abstractmethod
    def convert(self, config, val):
        pass
