

from pymodbus.constants import Endian


class BytesUplinkConverterConfig:
    def __init__(self, **kwargs):
        self.report_strategy = kwargs.get('reportStrategy')
        self.device_name = kwargs['deviceName']
        self.device_type = kwargs.get('deviceType', 'default')
        self.byte_order = Endian.BIG if kwargs.get('byteOrder', 'LITTLE').upper() == "BIG" else Endian.LITTLE
        self.word_order = Endian.BIG if kwargs.get('wordOrder', 'LITTLE').upper() == "BIG" else Endian.LITTLE
        self.telemetry = kwargs.get('timeseries', [])
        self.attributes = kwargs.get('attributes', [])

    def is_readable(self):
        return len(self.telemetry) > 0 or len(self.attributes) > 0
