

import re

from tests.unit.BaseUnitTest import BaseUnitTest
from iotplatform_gateway.connectors.bacnet.device import Device


class BACnetDeviceTests(BaseUnitTest):
    def test_get_address_regex_wildcard_star_colon_star_colon_star(self):
        address = "*:*:*"
        result = Device.get_address_regex(address)
        self.assertEqual(result, r".*")

    def test_get_address_regex_wildcard_star_colon_star(self):
        address = "*:*"
        result = Device.get_address_regex(address)
        self.assertEqual(result, Device.ALLOWED_WITH_ROUTERS_ADDRESSES_PATTERN)

    def test_get_address_regex_wildcard_star(self):
        address = "*"
        result = Device.get_address_regex(address)
        self.assertEqual(result, Device.ALLOWED_LOCAL_ADDRESSES_PATTERN_WITH_DEFAULT_PORT)

    def test_get_address_regex_pattern_with_custom_x_character(self):
        address = "192.168.X.X:47808"
        result = Device.get_address_regex(address)
        self.assertEqual(result, r"^192\.168\.\d+\.\d+(?::47808)?$")
        self.assertTrue(re.match(result, '192.168.2.3:47808'))
        self.assertTrue(re.match(result, '192.168.1.5'))

    def test_get_address_regex_pattern_with_port_wildcard(self):
        address = "192.168.X.X:*"
        result = Device.get_address_regex(address)
        self.assertEqual(result, r"^192\.168\.\d+\.\d+(:\d+)?$")

    def test_get_address_regex_wildcard_with_port(self):
        address = "*:6789"
        result = Device.get_address_regex(address)
        self.assertEqual(result,
                         Device.ALLOWED_LOCAL_ADDRESSES_PATTERN_WITH_CUSTOM_PORT.replace('{expectedPort}', '6789'))
        self.assertTrue(re.match(result, '192.168.1.1:6789'))
        self.assertTrue(re.match(result, '2001:6789'))
        self.assertFalse(re.match(result, '192.168.23.1'))

    def test_get_address_regex_colon_separated_two_parts_with_default_port(self):
        address = "192.168.1.1:47808"
        result = Device.get_address_regex(address)
        self.assertEqual(result, r"^192.168.1.1(?::47808)?$")
        self.assertTrue(re.match(result, '192.168.1.1:47808'))
        self.assertTrue(re.match(result, '192.168.1.1'))

    def test_get_address_regex_pattern_with_at_sign(self):
        address = "192.168.X.X:*@domain"
        result = Device.get_address_regex(address)
        self.assertEqual(result, r"^192\.168\.\d+\.\d+(:\d+)?$")
