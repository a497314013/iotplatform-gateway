

from typing import Union

from iotplatform_gateway.connectors.converter import Converter, abstractmethod
from iotplatform_gateway.gateway.entities.converted_data import ConvertedData


class OpcUaConverter(Converter):
    @abstractmethod
    def convert(self, config, val) -> Union[dict, ConvertedData]:
        pass
