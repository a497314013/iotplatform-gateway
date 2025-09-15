

from iotplatform_gateway.connectors.converter import Converter
from iotplatform_gateway.gateway.statistics.decorators import CollectStatistics


class SNMPDownlinkConverter(Converter):
    def __init__(self, config):
        self.__config = config

    @CollectStatistics(start_stat_type='allReceivedBytesFromTB',
                       end_stat_type='allBytesSentToDevices')
    def convert(self, config, data):
        return data["params"]
