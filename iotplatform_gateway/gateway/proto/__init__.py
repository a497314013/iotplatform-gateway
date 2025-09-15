

# Use the following command to generate python code from proto file;

#$ python3 -m grpc_tools.protoc -Iiotplatform_gateway/gateway/proto --python_out=iotplatform_gateway/gateway/proto/ --grpc_python_out=iotplatform_gateway/gateway/proto/ iotplatform_gateway/gateway/proto/messages.proto

# Update file messages_pb2_grpc.py:

# Replace:
# import messages_pb2 as messages__pb2
# With:
# import iotplatform_gateway.gateway.proto.messages_pb2 as messages__pb2
