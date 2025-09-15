

from iotplatform_gateway.connectors.converter import Converter, abstractmethod


class MqttUplinkConverter(Converter):

    @abstractmethod
    def convert(self, config, data):
        pass
