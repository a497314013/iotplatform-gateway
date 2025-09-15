

from setuptools import setup
from os import path

from iotplatform_gateway import version

current_directory = path.abspath(path.dirname(__file__))
with open(path.join(current_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    version=version.VERSION,
    name="iotplatform-gateway",
    author="IOTPlatform",
    author_email="info@seariiot.io",
    license="Apache Software License (Apache Software License 2.0)",
    description="IOTPlatform Gateway for IoT devices.",
    url="https://github.com/seariiot/iotplatform-gateway",
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    python_requires=">=3.10",
    packages=['iotplatform_gateway', 'iotplatform_gateway.gateway',
              'iotplatform_gateway.gateway.entities',
              'iotplatform_gateway.gateway.proto', 'iotplatform_gateway.gateway.grpc_service',
              'iotplatform_gateway.gateway.shell', 'iotplatform_gateway.gateway.statistics',
              'iotplatform_gateway.storage', 'iotplatform_gateway.storage.memory',
              'iotplatform_gateway.gateway.report_strategy', 'iotplatform_gateway.storage.file',
              'iotplatform_gateway.storage.sqlite',
              'iotplatform_gateway.connectors',
              'iotplatform_gateway.connectors.ble', 'iotplatform_gateway.extensions.ble',
              'iotplatform_gateway.connectors.socket', 'iotplatform_gateway.extensions.socket',
              'iotplatform_gateway.connectors.mqtt', 'iotplatform_gateway.extensions.mqtt',
              'iotplatform_gateway.connectors.xmpp', 'iotplatform_gateway.extensions.xmpp',
              'iotplatform_gateway.connectors.modbus', 'iotplatform_gateway.connectors.modbus.entities',
              'iotplatform_gateway.extensions.modbus',
              'iotplatform_gateway.connectors.opcua', 'iotplatform_gateway.extensions.opcua',
              'iotplatform_gateway.connectors.opcua.entities',
              'iotplatform_gateway.connectors.request', 'iotplatform_gateway.extensions.request',
              'iotplatform_gateway.connectors.ocpp', 'iotplatform_gateway.extensions.ocpp',
              'iotplatform_gateway.connectors.can', 'iotplatform_gateway.extensions.can',
              'iotplatform_gateway.connectors.odbc', 'iotplatform_gateway.extensions.odbc',
              'iotplatform_gateway.connectors.bacnet', 'iotplatform_gateway.connectors.bacnet.entities',
              'iotplatform_gateway.extensions.bacnet',
              'iotplatform_gateway.connectors.rest', 'iotplatform_gateway.extensions.rest',
              'iotplatform_gateway.connectors.snmp', 'iotplatform_gateway.extensions.snmp',
              'iotplatform_gateway.connectors.ftp', 'iotplatform_gateway.extensions.ftp',
              'iotplatform_gateway.connectors.knx', 'iotplatform_gateway.extensions.knx',
              'iotplatform_gateway.connectors.knx.entities',
              'iotplatform_gateway.tb_utility', 'iotplatform_gateway.extensions',
              'iotplatform_gateway.extensions.serial'
              ],
    install_requires=[
        'setuptools',
        'cryptography',
        'jsonpath-rw',
        'regex',
        'pip',
        'PyYAML',
        'orjson',
        'pybase64',
        'simplejson',
        'urllib3>=2.3.0',
        'requests>=2.32.3',
        'questionary',
        'pyfiglet',
        'termcolor',
        'mmh3',
        'grpcio',
        'protobuf',
        'python-dateutil',
        'cachetools',
        'tb-paho-mqtt-client>=2.1.2',
        'tb-mqtt-client==1.13.9',
        'packaging==23.1',
        'service-identity',
        'psutil'
    ],
    download_url='https://github.com/iotplatform/iotplatform-gateway/archive/%s.tar.gz' % version.VERSION,
    entry_points={
        'console_scripts': [
            'iotplatform-gateway = iotplatform_gateway.tb_gateway:daemon',
            'tb-gateway-configurator = iotplatform_gateway.gateway.configuration_wizard:configure',
            'tb-gateway-shell = iotplatform_gateway.gateway.shell:main'
        ]
    })
