

from threading import Thread
from time import time, sleep

from pymodbus.constants import Defaults

from iotplatform_gateway.connectors.modbus.bytes_modbus_downlink_converter import BytesModbusDownlinkConverter
from iotplatform_gateway.connectors.modbus.constants import *
from iotplatform_gateway.grpc_connectors.gw_grpc_msg_creator import GrpcMsgCreator
from iotplatform_gateway.grpc_connectors.modbus.bytes_modbus_uplink_converter import GrpcBytesModbusUplinkConverter
from iotplatform_gateway.tb_utility.tb_loader import TBModuleLoader


class Slave(Thread):
    def __init__(self, **kwargs):
        super().__init__()
        self._log = kwargs['logger']
        self.timeout = kwargs.get('timeout')
        self.name = kwargs['deviceName']
        self.poll_period = kwargs['pollPeriod'] / 1000

        self.byte_order = kwargs['byteOrder']
        self.word_order = kwargs.get('wordOrder')
        self.config = {
            'unitId': kwargs['unitId'],
            'deviceType': kwargs.get('deviceType', 'default'),
            'type': kwargs['type'],
            'host': kwargs.get('host'),
            'port': kwargs['port'],
            'byteOrder': kwargs['byteOrder'],
            'wordOrder': kwargs['wordOrder'],
            'timeout': kwargs.get('timeout', 35),
            'stopbits': kwargs.get('stopbits', Defaults.Stopbits),
            'bytesize': kwargs.get('bytesize', Defaults.Bytesize),
            'parity': kwargs.get('parity', Defaults.Parity),
            'strict': kwargs.get('strict', True),
            'retries': kwargs.get('retries', 3),
            'connection_attempt': 0,
            'last_connection_attempt_time': 0,
            'sendDataOnlyOnChange': kwargs.get('sendDataOnlyOnChange', False),
            'waitAfterFailedAttemptsMs': kwargs.get('waitAfterFailedAttemptsMs', 0),
            'connectAttemptTimeMs': kwargs.get('connectAttemptTimeMs', 0),
            'retry_on_empty': kwargs.get('retryOnEmpty', False),
            'retry_on_invalid': kwargs.get('retryOnInvalid', False),
            'method': kwargs.get('method', 'rtu'),
            'baudrate': kwargs.get('baudrate', 19200),
            'attributes': kwargs.get('attributes', []),
            'timeseries': kwargs.get('timeseries', []),
            'attributeUpdates': kwargs.get('attributeUpdates', []),
            'rpc': kwargs.get('rpc', []),
            'last_attributes': {},
            'last_telemetry': {}
        }

        self.__load_converters(kwargs['connector'], kwargs['connector_key'])

        self.callback = kwargs['callback']

        self.last_polled_time = None
        self.daemon = True

        self.start()

    def timer(self):
        self.callback(self)
        self.last_polled_time = time()

        while True:
            if time() - self.last_polled_time >= self.poll_period:
                self.callback(self)
                self.last_polled_time = time()

            sleep(.2)

    def run(self):
        self.timer()

    def get_name(self):
        return self.name

    def __load_converters(self, connector, connector_key):
        try:
            if self.config.get(UPLINK_PREFIX + CONVERTER_PARAMETER) is not None:
                converter = TBModuleLoader.import_module(connector.connector_type,
                                                         self.config[UPLINK_PREFIX + CONVERTER_PARAMETER])(self)
            else:
                converter = GrpcBytesModbusUplinkConverter({**self.config, 'deviceName': self.name})

            if self.config.get(DOWNLINK_PREFIX + CONVERTER_PARAMETER) is not None:
                downlink_converter = TBModuleLoader.import_module(connector.connector_type, self.config[
                    DOWNLINK_PREFIX + CONVERTER_PARAMETER])(self)
            else:
                downlink_converter = BytesModbusDownlinkConverter(self.config)

            if self.name not in GrpcMsgCreator.create_get_connected_devices_msg(connector_key):
                GrpcMsgCreator.create_device_connected_msg(device_name=self.name,
                                                           device_type=self.config.get(DEVICE_TYPE_PARAMETER))

            self.config[UPLINK_PREFIX + CONVERTER_PARAMETER] = converter
            self.config[DOWNLINK_PREFIX + CONVERTER_PARAMETER] = downlink_converter
        except Exception as e:
            self._log.exception(e)

    def __str__(self):
        return f'{self.name}'
