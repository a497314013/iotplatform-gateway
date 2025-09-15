

from abc import ABC, abstractmethod
from typing import Union

from iotplatform_gateway.gateway.entities.converted_data import ConvertedData


class Converter(ABC):

    @abstractmethod
    def convert(self, config, data) -> Union[dict, ConvertedData]:
        pass
