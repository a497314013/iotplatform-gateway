
from abc import abstractmethod

from iotplatform_gateway.connectors.converter import Converter


class AsyncBACnetConverter(Converter):
    @abstractmethod
    def convert(self, data):
        pass
