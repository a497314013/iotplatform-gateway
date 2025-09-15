

from iotplatform_gateway.gateway.proto.messages_pb2 import *


class GwMsgCallbacks:
    __CALLBACKS = {
        Response: None,
        ConnectorConfigurationMsg: None,
        GatewayAttributeUpdateNotificationMsg: None,
        GatewayAttributeResponseMsg: None,
        GatewayDeviceRpcRequestMsg: None,
        UnregisterConnectorMsg: None,
    }

    def set_callback(self,
                     received_response_cb=None,
                     received_connector_configuration_cb=None,
                     received_gateway_attribute_update_notification_cb=None,
                     received_gateway_attribute_response_cb=None,
                     received_gateway_device_rpc_request_cb=None,
                     received_unregister_connector_cb=None
                     ):
        if received_response_cb is not None:
            self.__CALLBACKS[Response] = received_response_cb
        if received_connector_configuration_cb is not None:
            self.__CALLBACKS[ConnectorConfigurationMsg] = received_connector_configuration_cb
        if received_gateway_attribute_update_notification_cb is not None:
            self.__CALLBACKS[GatewayAttributeUpdateNotificationMsg] = received_gateway_attribute_update_notification_cb
        if received_gateway_attribute_response_cb is not None:
            self.__CALLBACKS[GatewayAttributeResponseMsg] = received_gateway_attribute_response_cb
        if received_gateway_device_rpc_request_cb is not None:
            self.__CALLBACKS[GatewayDeviceRpcRequestMsg] = received_gateway_device_rpc_request_cb
        if received_unregister_connector_cb is not None:
            self.__CALLBACKS[UnregisterConnectorMsg] = received_unregister_connector_cb
