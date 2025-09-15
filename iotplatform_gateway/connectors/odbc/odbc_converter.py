

from iotplatform_gateway.connectors.converter import ABC, abstractmethod


class OdbcConverter(ABC):
    @abstractmethod
    def convert(self, config, data):
        pass
