

from ast import literal_eval
from urllib.parse import quote

from simplejson import dumps

from iotplatform_gateway.connectors.rest.rest_converter import RESTConverter
from iotplatform_gateway.gateway.statistics.decorators import CollectStatistics
from iotplatform_gateway.tb_utility.tb_utility import TBUtility


class JsonRESTDownlinkConverter(RESTConverter):
    def __init__(self, config, logger):
        self._log = logger
        self.__config = config

    @CollectStatistics(start_stat_type='allReceivedBytesFromTB',
                       end_stat_type='allBytesSentToDevices')
    def convert(self, config, data):
        try:
            if data["data"].get("id") is None:
                attribute_key = list(data["data"].keys())[0]
                attribute_value = list(data["data"].values())[0]

                result = {
                    "url": self.__config["requestUrlExpression"]
                    .replace("${attributeKey}", quote(attribute_key))
                    .replace("${attributeValue}", quote(str(attribute_value)))
                    .replace("${deviceName}", quote(data["device"])),
                    "data": self.__config["valueExpression"]
                    .replace("${attributeKey}", attribute_key)
                    .replace("${attributeValue}", str(attribute_value))
                    .replace("${deviceName}", data["device"])}
            else:
                rest_id = str(data["data"]["id"])
                method_name = data["data"]["method"]

                result = {
                    "url": self.__config["requestUrlExpression"].replace("${restId}", rest_id)
                    .replace("${methodName}", method_name)
                    .replace("${deviceName}", quote(data["device"])),
                    "data": self.__config["valueExpression"].replace("${restId}", rest_id)
                    .replace("${methodName}", method_name)
                    .replace("${deviceName}", data["device"])
                }

            result['url'] = TBUtility.replace_params_tags(result['url'], data)

            data_tags = TBUtility.get_values(config.get('valueExpression'), data['data'], 'params',
                                             get_tag=True)
            data_values = TBUtility.get_values(config.get('valueExpression'), data['data'], 'params',
                                               expression_instead_none=True)

            for (tag, value) in zip(data_tags, data_values):
                result['data'] = result["data"].replace('${' + tag + '}', str(value))

            result["data"] = dumps(literal_eval(result["data"]))
            return result
        except Exception as e:
            self._log.exception(e)
