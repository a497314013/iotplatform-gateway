

from iotplatform_gateway.tb_utility.tb_utility import TBUtility


class DeviceInfo:
    def __init__(self, device_info_config, device_details):
        self.device_name = self.__parse_device_name(device_info_config, device_details)
        self.device_type = self.__parse_device_type(device_info_config, device_details)

    def __parse_device_name(self, config, data):
        if config.get('deviceNameExpressionSource', 'expression') == 'expression':
            return self.__parse_device_info(config['deviceNameExpression'], data)

        return config['deviceNameExpression']

    def __parse_device_type(self, config, data):
        if config.get('deviceProfileExpressionSource', 'expression') == 'expression':
            return self.__parse_device_info(config.get('deviceProfileExpression', 'default'), data)

        return config.get('deviceProfileExpression', 'default')

    @staticmethod
    def __parse_device_info(expression, data):
        result_tags = TBUtility.get_values(expression, data.as_dict, get_tag=True)
        result_values = TBUtility.get_values(expression, data.as_dict, expression_instead_none=True)

        result = expression
        for (result_tag, result_value) in zip(result_tags, result_values):
            is_valid_key = "${" in expression and "}" in expression
            result = result.replace('${' + str(result_tag) + '}',
                                    str(result_value)) if is_valid_key else result_tag

        return result
