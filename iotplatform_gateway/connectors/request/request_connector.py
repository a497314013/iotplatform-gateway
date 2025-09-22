import copy
import json
from iotplatform_gateway.gateway.constants import ReportStrategy
from queue import Queue
from random import choice
from re import fullmatch
from string import ascii_lowercase
from threading import Thread
from time import sleep, time

from iotplatform_gateway.gateway.entities.converted_data import ConvertedData
from iotplatform_gateway.gateway.statistics.statistics_service import StatisticsService
from iotplatform_gateway.tb_utility.tb_loader import TBModuleLoader
from iotplatform_gateway.tb_utility.tb_utility import TBUtility
from iotplatform_gateway.tb_utility.tb_logger import init_logger

try:
    from requests import Timeout, request
except ImportError:
    print("Requests library not found - installing...")
    TBUtility.install_package("requests")
    from requests import Timeout, request
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException, JSONDecodeError

from iotplatform_gateway.connectors.connector import Connector
from iotplatform_gateway.connectors.request.json_request_uplink_converter import JsonRequestUplinkConverter
from iotplatform_gateway.connectors.request.json_request_downlink_converter import JsonRequestDownlinkConverter


class RequestConnector(Connector, Thread):
    def __init__(self, gateway, config, connector_type):
        super().__init__()
        # 新增：mapping缓存存储
        self.__cache = {} # key: mappingName, value: dict of cached attributes
        self.__rpc_requests = []
        self.__config = config
        self.__id = self.__config.get('id')
        self._connector_type = connector_type
        self.__gateway = gateway
        self.name = self.__config.get("name", "".join(choice(ascii_lowercase) for _ in range(5)))
        self._log = init_logger(self.__gateway, self.name, self.__config.get('logLevel', 'INFO'),
                                enable_remote_logging=self.__config.get('enableRemoteLogging', False),
                                is_connector_logger=True)
        self._converter_log = init_logger(self.__gateway, self.name + '_converter',
                                          self.__config.get('logLevel', 'INFO'),
                                          enable_remote_logging=self.__config.get('enableRemoteLogging', False),
                                          is_converter_logger=True, attr_name=self.name)
        self.__security = HTTPBasicAuth(self.__config["security"]["username"], self.__config["security"]["password"]) if \
            self.__config["security"]["type"] == "basic" else None
        self.__host = None
        self.__service_headers = {}
        if "http://" in self.__config["host"].lower() or "https://" in self.__config["host"].lower():
            self.__host = self.__config["host"]
        else:
            self.__host = "http://" + self.__config["host"]
        self.__ssl_verify = self.__config.get("SSLVerify", False)
        self.daemon = True
        self.__connected = False
        self.__stopped = False
        self.__requests_in_progress = []
        self.__convert_queue = Queue(1000000)
        self.__attribute_updates = []
        self.__fill_attribute_updates()
        self.__fill_rpc_requests()
        self.__fill_requests()

    def run(self):
        while not self.__stopped:
            request_sent = False
            if self.__requests_in_progress:
                for req in self.__requests_in_progress:
                    if time() >= req["next_time"]:
                        thread = Thread(target=self.__send_request, args=(req, self.__convert_queue, self._log),
                                        daemon=True,
                                        name="Request to endpoint \'%s\' Thread" % (req["config"].get("url")))
                        thread.start()
                        request_sent = True
            if not request_sent:
                sleep(.2)
            self.__process_data()

    def on_attributes_update(self, content):
        try:
            for attribute_request in self.__attribute_updates:
                if fullmatch(attribute_request["deviceNameFilter"], content["device"]) and fullmatch(
                        attribute_request["attributeFilter"], list(content["data"].keys())[0]):
                    converted_data = attribute_request["converter"].convert(attribute_request, content)
                    response_queue = Queue(1)
                    request_dict = {"config": {**attribute_request,
                                               **converted_data},
                                    "request": request,
                                    "withResponse": True}
                    attribute_update_request_thread = Thread(target=self.__send_request,
                                                             args=(request_dict, response_queue, self._log),
                                                             daemon=True,
                                                             name="Attribute request to %s" % (converted_data["url"]))
                    attribute_update_request_thread.start()
                    attribute_update_request_thread.join()
                    if not response_queue.empty():
                        response = response_queue.get_nowait()
                        self._log.debug(response)
                    del response_queue
        except Exception as e:
            self._log.exception(e)

    def server_side_rpc_handler(self, content):
        try:
            # check if RPC method is reserved get/set
            self.__check_and_process_reserved_rpc(content)

            for rpc_request in self.__rpc_requests:
                if fullmatch(rpc_request["deviceNameFilter"], content["device"]) and fullmatch(
                        rpc_request["methodFilter"], content["data"]["method"]):
                    self.__process_rpc(rpc_request, content)
        except Exception as e:
            self._log.exception(e)

    def __process_rpc(self, rpc_request, content):
        converted_data = rpc_request["converter"].convert(rpc_request, content)
        response_queue = Queue(1)
        request_dict = {"config": {**rpc_request,
                                   **converted_data},
                        "request": request,
                        "withResponse": True}
        rpc_request_thread = Thread(target=self.__send_request,
                                    args=(request_dict, response_queue, self._log),
                                    daemon=True,
                                    name="RPC request to %s" % (converted_data["url"]))
        rpc_request_thread.start()
        rpc_request_thread.join()
        if not response_queue.empty():
            response = response_queue.get_nowait()

            if rpc_request.get('responseValueExpression'):
                response_value_expression = rpc_request['responseValueExpression']
                values = TBUtility.get_values(response_value_expression, response.json(),
                                              expression_instead_none=True)
                values_tags = TBUtility.get_values(
                    response_value_expression, response.json(), get_tag=True)
                full_value = response_value_expression
                for (value, value_tag) in zip(values, values_tags):
                    is_valid_value = "${" in response_value_expression and "}" in response_value_expression

                    full_value = full_value.replace('${' + str(value_tag) + '}', str(value)) if is_valid_value else str(value)

                self.__gateway.send_rpc_reply(device=content["device"], req_id=content["data"]["id"],
                                              content={'result': full_value})
                del response_queue
                return

            self.__gateway.send_rpc_reply(device=content["device"], req_id=content["data"]["id"],
                                          content={'result': response.text})
            del response_queue
            return

        self.__gateway.send_rpc_reply(device=content["device"], req_id=content["data"]["id"],
                                      success_sent=True)

        del response_queue

    def __check_and_process_reserved_rpc(self, content):
        rpc_method_name = content["data"]["method"]

        if rpc_method_name == 'get' or rpc_method_name == 'set':
            params = self.__parse_reserved_rpc_params(rpc_method_name, content["data"]["params"])

            rpc_request = self.__format_rpc_reqeust(params)

            rpc_request['converter'] = JsonRequestDownlinkConverter(rpc_request, self._converter_log)

            self.__process_rpc(rpc_request, content)

    def __parse_reserved_rpc_params(self, rpc_method_name, params):
        result_params = {}
        for param in params.split(';'):
            try:
                (key, value) = param.split('=')
            except ValueError:
                continue

            if key and value:
                result_params[key] = value

        if rpc_method_name == 'set':
            result_params['requestValueExpression'] = result_params.pop('value', None)

        return result_params

    def __format_rpc_reqeust(self, params):
        return {
            'requestUrlExpression': params['requestUrlExpression'],
            'responseTimeout': params.get('responseTimeout', 1),
            'httpMethod': params.get('httpMethod', 'GET'),
            'requestValueExpression': params.get('requestValueExpression', '${params}'),
            'responseValueExpression': params.get('responseValueExpression', None),
            'timeout': params.get('timeout', 0.5),
            'tries': params.get('tries', 3),
            'httpHeaders': params.get('httpHeaders', {
                'Content-Type': 'application/json'
            }),
        }

    def __fill_requests(self):
        self._log.debug(self.__config["mapping"])
        for endpoint in self.__config["mapping"]:
            try:
                self._log.debug(endpoint)
                converter = None
                if endpoint["converter"]["type"] == "custom":
                    module = TBModuleLoader.import_module(self._connector_type, endpoint["converter"]["extension"])
                    if module:
                        self._log.debug('Custom converter for url %s - found!', endpoint["url"])
                        converter = module(endpoint, self._converter_log)
                    else:
                        self._log.error(
                            "\n\nCannot find extension module for %s url.\nPlease check your configuration.\n",
                            endpoint["url"])
                else:
                    converter = JsonRequestUplinkConverter(endpoint, self._log)
                self.__requests_in_progress.append({"config": endpoint,
                                                    "converter": converter,
                                                    "next_time": time(),
                                                    "mapping_name": endpoint.get("name"),
                                                    "request": request})
            except Exception as e:
                self._log.exception(e)

    def __fill_attribute_updates(self):
        for attribute_request in self.__config.get("attributeUpdates", []):
            if attribute_request.get("converter") is not None:
                converter = TBModuleLoader.import_module("request", attribute_request["converter"])(attribute_request,
                                                                                                    self._converter_log)
            else:
                converter = JsonRequestDownlinkConverter(attribute_request, self._converter_log)
            attribute_request_dict = {**attribute_request, "converter": converter}
            self.__attribute_updates.append(attribute_request_dict)

    def __fill_rpc_requests(self):
        for rpc_request in self.__config.get("serverSideRpc", []):
            if rpc_request.get("converter") is not None:
                converter = TBModuleLoader.import_module("request", rpc_request["converter"])(rpc_request, self._converter_log)
            else:
                converter = JsonRequestDownlinkConverter(rpc_request, self._converter_log)
            rpc_request_dict = {**rpc_request, "converter": converter}
            self.__rpc_requests.append(rpc_request_dict)

    def __send_request(self, request, converter_queue, logger):
        url = ""
        try:
            request["next_time"] = time() + request["config"].get("scanPeriod", 10)
            if request.get("converter") is None and isinstance(request["config"].get("converter"), dict):
                logger.error("Converter for request to '%s' endpoint is not defined. Request will be skipped.", request["config"].get("url"))
                return
            request_url_from_config = request["config"]["url"]
            request_url_from_config = (
                str("/" + request_url_from_config)
                if not request_url_from_config.startswith("/")
                   and not request_url_from_config.startswith("http")
                else request_url_from_config
            )
            logger.debug("Obtained request url from config - %s ", request_url_from_config)
            url, response = self.__execute_request(request, request_url_from_config, logger)

            if request.get('withResponse'):
                converter_queue.put(response)
                return

            if response and response.ok:
                if not converter_queue.full():
                    config_converter_data = [url, request["converter"]]
                    try:
                        json_response = response.json()

                        # Unpack data if dataUnpackExpression is defined in config
                        # This allows to unpack JSON responses that have final data at a sub key on any level
                        # {
                        #   "device": [...]
                        # }
                        data_unpack_expression = request["config"].get("dataUnpackExpression")
                        if data_unpack_expression:
                            json_response = TBUtility.get_value(data_unpack_expression, json_response, value_type="json")

                        config_converter_data.append(json_response)
                    except UnicodeDecodeError:
                        config_converter_data.append(response.content)
                    except JSONDecodeError:
                        config_converter_data.append(response.content)

                    if len(config_converter_data) == 3:
                        # process sub mapping
                        if request["config"].get("subMapping"):
                            try:
                                self.__process_sub_mappings(request, url, config_converter_data[2], logger)
                            except Exception as e:
                                logger.exception("Error while processing subMapping: %s", e)
                        # Process sub requests if defined in config
                        if request["config"].get("subRequests"):
                            self.__process_sub_requests(request, url, config_converter_data[2], logger)
                        mapping_name = request.get("mapping_name")
                        self.__convert_data(url, request["converter"], json_response, request["config"], mapping_name)
            else:
                logger.error("Request to URL: %s finished with code: %i", url, response.status_code)
        except Timeout:
            logger.error("Timeout error on request %s.", url)
        except RequestException as e:
            logger.error("Cannot connect to %s. Connection error.", url)
            logger.debug(e)
        except ConnectionError:
            logger.error("Cannot connect to %s. Connection error.", url)
        except Exception as e:
            logger.exception(e)

    def __replace_from_item(self, text: str, item: dict) -> str:
        import re
        new_text = text

        # 匹配 ${...} 占位符
        matches = re.findall(r"\$\{([^\}]+)\}", text)
        for match in matches:
            try:
                # 用 get_value 取值，支持 JSON 路径/表达式
                value = TBUtility.get_value(match, item, value_type="json")
                if value is not None:
                    new_text = new_text.replace(f"${{{match}}}", str(value))
            except Exception:
                new_text = text
        return new_text

    def __process_sub_mappings(self, request, parent_url, data, logger):
        """
        新增：处理 mapping 下的 subMapping 配置
        - request: 父请求对象（包含 config）
        - parent_url: 父请求构成的 url（用于相对地址拼接）
        - data: 父请求的 JSON 响应（可以是 list 或 dict）
        """
        # 支持 data 为 list 或单个对象
        try:
            config = request["config"]
            sub_mapping = config.get("subMapping")
            if not sub_mapping:
                return

            # 支持 subMapping 为 dict（单条）或 list（多条）
            sub_mappings = sub_mapping if isinstance(sub_mapping, list) else [sub_mapping]

            # 逐个 subMapping 处理
            for sm in sub_mappings:
                loop_expr = sm.get("loop")
                if not loop_expr:
                    logger.warning("subMapping missing 'loop' expression - skipping")
                    continue

                # strip ${...} 如果存在
                expr = loop_expr
                if isinstance(loop_expr, str) and loop_expr.startswith("${") and loop_expr.endswith("}"):
                    expr = loop_expr[2:-1]

                # 从父响应中获取 loop 对应的 list（使用 TBUtility.get_value）
                loop_list = TBUtility.get_value(expr, data, value_type="json")
                if loop_list is None:
                    logger.debug("subMapping loop returned None for expr %s", expr)
                    continue
                if not isinstance(loop_list, list):
                    logger.error("subMapping.loop must evaluate to a list, got: %s (expr=%s)", type(loop_list), expr)
                    continue

                # 对 loop_list 中每个元素发起子请求
                for item in loop_list:
                    # construct sub request config as a deep copy so we don't mutate original
                    sub_conf = copy.deepcopy(sm)
                    # remove loop from sub_conf so it won't be used as request field
                    sub_conf.pop("loop", None)

                    # replace ${result.xxx} placeholders in URL / data / headers using __replace_cache_values
                    sub_url_raw = sub_conf.get("url", "")
                    try:
                        request_url_from_config = self.__replace_from_item(sub_url_raw, item)
                    except Exception:
                        # fallback: if TBUtility fails, do a simple str replace for ${result.}
                        request_url_from_config = sub_url_raw
                    # allow templates referencing item via ${result.xxx}

                    # if relative url, make absolute relative to parent_url
                    if not request_url_from_config.lower().startswith("http"):
                        if not request_url_from_config.startswith("/"):
                            request_url_from_config = "/" + request_url_from_config
                        request_url_from_config = self.__host + request_url_from_config

                    logger.debug("subMapping: sending sub request to %s", request_url_from_config)

                    # prepare a temporary request wrapper (copy parent request but override config)
                    temp_request = {
                        "config": copy.deepcopy(request["config"]),  # base on parent config
                        "request": request["request"]
                    }
                    # override specific fields from sub_conf
                    # allowed overrides: url/httpMethod/httpHeaders/data/timeout/allowRedirects/ssl etc.
                    for key in ("httpMethod", "httpHeaders", "data", "timeout", "allowRedirects", "SSLVerify",
                                "security"):
                        if key in sub_conf:
                            temp_request["config"][key] = sub_conf[key]
                    # ensure converter for sub request is the sub_conf.converter
                    temp_request["config"]["converter"] = sub_conf.get("converter", {})

                    # Before execute: replace ${result.xxx} in headers and data if they exist
                    if temp_request["config"].get("httpHeaders"):
                        new_headers = {}
                        for hk, hv in temp_request["config"]["httpHeaders"].items():
                            try:
                                new_headers[hk] = self.__replace_from_item(hv, item)
                            except Exception:
                                new_headers[hk] = hv

                        temp_request["config"]["httpHeaders"] = new_headers

                    if temp_request["config"].get("data") and isinstance(temp_request["config"].get("data"), str):
                        try:
                            temp_request["config"]["data"] = self.__replace_from_item(temp_request["config"]["data"], item)
                        except Exception:
                            pass

                    # Now execute the sub request (this will also apply cache-based replacements via __execute_request)
                    try:
                        sub_url, sub_resp = self.__execute_request(temp_request, request_url_from_config, logger)
                    except Exception as e:
                        logger.exception("subMapping __execute_request failed: %s", e)
                        continue

                    # If response ok -> convert and push to convert queue
                    if sub_resp and sub_resp.ok:
                        try:
                            sub_json = sub_resp.json()
                        except Exception:
                            sub_json = sub_resp.content

                        # Instantiate converter for subMapping (support custom converters)
                        sub_converter = None
                        conv_conf = temp_request["config"].get("converter", {})
                        if isinstance(conv_conf, dict) and conv_conf.get("type") == "custom":
                            module = TBModuleLoader.import_module(self._connector_type, conv_conf.get("extension"))
                            if module:
                                sub_converter = module(sub_conf, self._converter_log)
                            else:
                                logger.error("Cannot find custom converter module for subMapping - skipping")
                                continue
                        else:
                            # JsonRequestUplinkConverter expects the full endpoint config,
                            # use sub_conf as endpoint for converter instantiation
                            try:
                                sub_converter = JsonRequestUplinkConverter(sub_conf, self._log)
                            except Exception as e:
                                logger.exception("Error creating JsonRequestUplinkConverter for subMapping: %s", e)
                                continue

                        # sub_json might be list or single object
                        if isinstance(sub_json, list):
                            for sub_item in sub_json:
                                self.__add_ts(sub_item)
                                try:
                                    converted = sub_converter.convert(sub_url, sub_item)
                                    # 推送到 convert queue（不传 mapping_name）
                                    self.__convert_queue.put(converted)
                                except Exception as e:
                                    logger.exception("Error converting subMapping response item: %s", e)
                        else:
                            self.__add_ts(sub_json)
                            try:
                                converted = sub_converter.convert(sub_url, sub_json)
                                self.__convert_queue.put(converted)
                            except Exception as e:
                                logger.exception("Error converting subMapping response: %s", e)

                    else:
                        logger.debug("subMapping request to %s finished with code: %s", request_url_from_config,
                                     getattr(sub_resp, "status_code", None))

        except Exception as e:
            logger.exception("Exception in __process_sub_mappings: %s", e)

    def __execute_request(self, request, request_url, logger):
        url = self.__host + request_url if not request_url.lower().startswith("http") else request_url
        # 替换url
        url = self.__replace_cache_values(url)

        request_timeout = request["config"].get("timeout", 1)
        params = {
            "method": request["config"].get("httpMethod", "GET"),
            "url": url,
            "timeout": request_timeout,
            "allow_redirects": request["config"].get("allowRedirects", False),
            "verify": self.__ssl_verify,
            "auth": self.__security,
            "data": request["config"].get("data", {})
        }

        logger.debug("Full url request has been formed - %s", url)

        if request["config"].get("httpHeaders") is not None:
            params["headers"] = request["config"]["httpHeaders"]

        # 替换httpHeaders中的值
        if "headers" in params and params["headers"]:
            headers = {}
            for k, v in params["headers"].items():
                if isinstance(v, str):
                    headers[k] = self.__replace_cache_values(v)
                else:
                    headers[k] = v
            params["headers"] = headers

        logger.debug("Request to %s will be sent", url)


        if isinstance(params["data"], str):
            # 替换data中的值
            params["data"] = self.__replace_cache_values(params["data"])
            params["data"] = params["data"].encode("utf-8")
        else:
            params["data"] = json.dumps(params["data"])
            # 替换data中的值
            params["data"] = self.__replace_cache_values(params["data"])

        logger.trace("Request params: %s", params)
        response = request["request"](**params)

        return url, response

    def __replace_cache_values(self, text: str):
        import re
        new_text = text  # 新建副本，不修改原始 text
        matches = re.findall(r"\$\{([^.]+)\.([^\}]+)\}", text)
        for mapping_name, key in matches:
            value = self.__cache.get(mapping_name, {}).get(key, "")
            new_text = new_text.replace(f"${{{mapping_name}.{key}}}", str(value))
        return new_text

    def __convert_data(self, url, converter, data, config, mapping_name=None):
        try:
            #url, converter, data = data
            data_to_send = []

            StatisticsService.count_connector_message(self.name, stat_parameter_name='connectorMsgsReceived')
            StatisticsService.count_connector_bytes(self.name, data, stat_parameter_name='connectorBytesReceived')

            if isinstance(data, list):
                for data_item in data:
                    self.__add_ts(data_item)
                    converted_data = converter.convert(url, data_item)
                    # 存 cache
                    if mapping_name:
                        self.__update_cache(mapping_name, converted_data,config)
                    data_to_send.append(converted_data)
            else:
                self.__add_ts(data)
                converted_data = converter.convert(url, data)
                if mapping_name:
                    self.__update_cache(mapping_name, converted_data,config)
                data_to_send.append(converted_data)

            for to_send in data_to_send:
                self.__convert_queue.put(to_send)

        except Exception as e:
            self._log.exception(e)

    def __update_cache(self, mapping_name, converted_data,config):
        # 1. 缓存 attributes
        if hasattr(converted_data, "attributes") and converted_data.attributes:
            attr_defs = config.get("converter", {}).get("attributes", [])
            for attr_def in attr_defs:
                if attr_def.get("cache"):
                    key = attr_def["key"]
                    for dp_key, dp_value in converted_data.attributes.values.items():
                        if getattr(dp_key, "key", None) == key:
                            self.__cache.setdefault(mapping_name, {})[key] = dp_value
                            break

        # telemetry
        if hasattr(converted_data, "telemetry") and converted_data.telemetry:
            telem_defs = config.get("converter", {}).get("telemetry", [])
            for telem_def in telem_defs:
                if telem_def.get("cache"):
                    key = telem_def["key"]
                    for dp_key, dp_value in converted_data.telemetry.values.items():
                        if getattr(dp_key, "key", None) == key:
                            self.__cache.setdefault(mapping_name, {})[key] = dp_value
                            break

    def __add_ts(self, data):
        if isinstance(data, list):
            for item in data:
                self.__add_ts(item)
        elif isinstance(data, dict):
            if data.get("ts") is None:
                data["ts"] = int(time() * 1000)

    # def __process_data(self):
    #     try:
    #         if not self.__convert_queue.empty():
    #             data: ConvertedData = self.__convert_queue.get()
    #             if data and (data.attributes_datapoints_count > 0 or data.telemetry_datapoints_count > 0):
    #                 self.__gateway.send_to_storage(self.get_name(), self.get_id(), data)
    #
    #     except Exception as e:
    #         self._log.exception(e)

    def __process_data(self):
        try:
            if not self.__convert_queue.empty():
                data: ConvertedData = self.__convert_queue.get()
                # 移除 attributes 中 report_strategy 为 DISABLED 的 datapoints
                if hasattr(data, "attributes") and data.attributes:
                    keys_to_remove = [dp_key for dp_key in data.attributes.values
                                      if getattr(dp_key.report_strategy, "report_strategy",
                                                 None) == ReportStrategy.DISABLED]
                    for dp_key in keys_to_remove:
                        del data.attributes.values[dp_key]

                # 移除 telemetry 中 report_strategy 为 DISABLED 的 datapoints
                if hasattr(data, "telemetry") and data.telemetry:
                    for entry in data.telemetry:
                        keys_to_remove = [dp_key for dp_key in entry.values
                                          if getattr(dp_key.report_strategy, "report_strategy",
                                                     None) == ReportStrategy.DISABLED]
                        for dp_key in keys_to_remove:
                            del entry.values[dp_key]

                # 如果移除后还有数据再上报
                if (data.attributes_datapoints_count > 0 or data.telemetry_datapoints_count > 0):
                    self.__gateway.send_to_storage(self.get_name(), self.get_id(), data)

        except Exception as e:
            self._log.exception(e)

    def get_id(self):
        return self.__id

    def get_name(self):
        return self.name

    def get_type(self):
        return self._connector_type

    def is_connected(self):
        return self.__connected

    def is_stopped(self):
        return self.__stopped

    def open(self):
        self.__stopped = False
        self.start()

    def close(self):
        self.__stopped = True
        self._log.info("%r has been stopped.", self.name)
        self._log.stop()

    def get_config(self):
        return self.__config

    def __process_sub_requests(self, request, url, data, logger):
        datatypes = {"attributes": "attributes",
                     "telemetry": "telemetry"}
        data = data if isinstance(data, list) else [data]

        for data_item in data:
            for datatype in datatypes:
                for datatype_object_config in request["config"]["converter"].get(datatype, []):
                    # Check if a sub request for key is needed
                    key = datatype_object_config.get("key")
                    if key in request["config"].get("subRequests", {}):
                        request_url_from_config = TBUtility.replace_params_tags(request["config"]["subRequests"][key]["url"],
                                                                                {"data": data_item})

                        if not request_url_from_config.lower().startswith("http"):
                            if not request_url_from_config.startswith("/"):
                                request_url_from_config = "/" + request_url_from_config
                            request_url_from_config = url + request_url_from_config
                        logger.debug("Sub request needed for key %s with url %s", key, request_url_from_config)

                        response = self.__send_sub_request(request, request_url_from_config, logger)
                        logger.debug("Sub request response: %s", response)

                        # Only if a response is available, process it
                        if response:
                            result = response
                            # Make processing function available if defined and call it
                            processing_function = request["config"]["subRequests"][key].get("processingFunction")
                            if processing_function:
                                logger.trace("Processing sub request response with function:\n%s", processing_function)
                                local_scope = {}
                                exec(processing_function, {}, local_scope)
                                result = local_scope["process_data"](response, key)
                            # Update data with result of sub request
                            data_item.update(result)
                            logger.debug("Data after sub request processing: %s", data_item)

    def __send_sub_request(self, request, sub_request_url, logger):
        url = ""
        try:
            url, response = self.__execute_request(request, sub_request_url, logger)
            if response and response.ok:
                try:
                    return response.json()
                except UnicodeDecodeError:
                    return response.content
                except JSONDecodeError:
                    return response.content
            else:
                logger.error("Request to URL: %s finished with code: %i", url, response.status_code)
        except Timeout:
            logger.error("Timeout error on request %s.", url)
        except RequestException as e:
            logger.error("Cannot connect to %s. Connection error.", url)
            logger.debug(e)
        except ConnectionError:
            logger.error("Cannot connect to %s. Connection error.", url)
        except Exception as e:
            logger.exception(e)
