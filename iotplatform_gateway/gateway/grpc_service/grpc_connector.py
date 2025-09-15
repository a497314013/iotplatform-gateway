


from iotplatform_gateway.connectors.connector import Connector
from iotplatform_gateway.gateway.constant_enums import DownlinkMessageType
from iotplatform_gateway.gateway.grpc_service.tb_grpc_manager import TBGRPCServerManager
from iotplatform_gateway.gateway.grpc_service.grpc_downlink_converter import GrpcDownlinkConverter


class GrpcConnector(Connector):
    def __init__(self, gateway, config, tb_grpc_server_manager: TBGRPCServerManager, session_id):
        self.name = None
        self.__id = config.get("id")
        self.__server_manager = tb_grpc_server_manager
        self.__session_id = session_id
        self.__downlink_converter = GrpcDownlinkConverter()

    def setName(self, name):
        self.name = name

    def open(self):
        pass

    def close(self):
        converter_config = {"message_type": DownlinkMessageType.UnregisterConnectorMsg}
        message_to_connector = self.__downlink_converter.convert(converter_config, "")
        self.__server_manager.write(self.name, message_to_connector, self.__session_id)

    def get_id(self):
        return self.__id

    def get_name(self):
        return self.name

    def is_connected(self):
        pass

    def on_attributes_update(self, content):
        converter_config = {"message_type": DownlinkMessageType.GatewayAttributeUpdateNotificationMsg}
        message_to_connector = self.__downlink_converter.convert(converter_config, content)
        self.__server_manager.write(self.name, message_to_connector, self.__session_id)

    def server_side_rpc_handler(self, content):
        converter_config = {"message_type": DownlinkMessageType.GatewayDeviceRpcRequestMsg}
        message_to_connector = self.__downlink_converter.convert(converter_config, content)
        self.__server_manager.write(self.name, message_to_connector, self.__session_id)

    @property
    def statistics(self):
        return self.__server_manager.get_connector_statistics(self.__session_id)
