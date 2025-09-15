

class UplinkConverterConfig:
    def __init__(self, config, device_info, device_details):
        self.__config = config

        self.device_details = device_details
        self.device_name = device_info.device_name
        self.device_type = device_info.device_type
        self.__objects_to_read = self.__get_objects_to_read()
        self.report_strategy = self.__config.get('reportStrategy', {})

    def __get_objects_to_read(self):
        objects_to_read = []

        for section in ('attributes', 'timeseries'):
            section_config = self.__config.get(section, [])

            if section_config != '*':
                for item in section_config:
                    is_local_discovery_config = list(filter(lambda key_value: key_value == '*', item.values()))
                    if len(is_local_discovery_config) == 0:
                        item = {**item, 'type': section}

                        if item.get('objectType') is None:
                            continue

                        if item['objectType'] == 'device':
                            item['objectId'] = self.device_details.object_id

                        objects_to_read.append(item)

        return objects_to_read

    @property
    def objects_to_read(self):
        return self.__objects_to_read
