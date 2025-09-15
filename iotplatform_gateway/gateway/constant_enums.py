

from enum import Enum


class DeviceActions(Enum):
    UNKNOWN = 0,
    CONNECT = 1,
    DISCONNECT = 2


class DownlinkMessageType(Enum):
    Response = 0,
    ConnectorConfigurationMsg = 1,
    GatewayAttributeUpdateNotificationMsg = 2,
    GatewayAttributeResponseMsg = 3,
    GatewayDeviceRpcRequestMsg = 4,
    UnregisterConnectorMsg = 5,
    ConnectorGetConnectedDevicesResponseMsg = 6


class Status(Enum):
    FAILURE = 1,
    NOT_FOUND = 2,
    SUCCESS = 3,
    NO_NEW_DATA = 4
    FORBIDDEN_DEVICE = 5
