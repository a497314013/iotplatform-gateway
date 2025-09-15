

import sys
from os import curdir, listdir, mkdir, path, environ

from iotplatform_gateway.gateway.constants import DEV_MODE_PARAMETER_NAME, TB_GW_DEV_DEBUG_SERVER_PORT
from iotplatform_gateway.gateway.tb_gateway_service import TBGatewayService
from iotplatform_gateway.gateway.hot_reloader import HotReloader
from iotplatform_gateway.tb_utility.tb_utility import TBUtility


def is_running_under_pycharm():
    return (
        "PYCHARM_HOSTED" in environ
        or "_pydevd_bundle" in sys.modules
    )

def main():
    is_dev_mode = TBUtility.str_to_bool(environ.get(DEV_MODE_PARAMETER_NAME, 'false'))

    if is_dev_mode and not is_running_under_pycharm:
        run_debug_server()

    if "logs" not in listdir(curdir):
        mkdir("logs")

    try:
        hot_reload = bool(sys.argv[1])
    except IndexError:
        hot_reload = False

    if hot_reload:
        HotReloader(TBGatewayService)
    else:
        config_path = __get_config_path(path.dirname(path.abspath(__file__)) + '/config/'.replace('/', path.sep))
        TBGatewayService(config_path + 'tb_gateway.json')


def daemon():
    config_path = __get_config_path("/etc/iotplatform-gateway/config/".replace('/', path.sep))
    TBGatewayService(config_path + "tb_gateway.json")


def __get_config_path(default_config_path):
    config_path = environ.get("TB_GW_CONFIG_DIR", default_config_path)
    if not config_path.endswith(path.sep):
        config_path += path.sep
    return config_path


def run_debug_server():
    try:
        import debugpy
    except ImportError:
        TBUtility.install_package("debugpy")
        import debugpy

    debugpy_port = int(environ.get("TB_GW_DEV_DEBUG_SERVER", TB_GW_DEV_DEBUG_SERVER_PORT))
    debugpy.listen(("0.0.0.0", debugpy_port))


if __name__ == '__main__':
    main()
