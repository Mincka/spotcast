"""Module to test the set_device_options function"""

from unittest import TestCase

from custom_components.spotcast.config_flow_classes.options_flow_handler \
    import SpotcastOptionsFlowHandler


class TestOptionsSaved(TestCase):

    def setUp(self):
        self.handler = SpotcastOptionsFlowHandler()
        self.handler._options = {
            "is_default": False,
            "base_refresh_rate": 30,
        }

        self.handler.set_device_options({
            "set_default": False,
            "base_refresh_rate": 30,
            "stale_device_timeout": 3,
            "device_filter_mode": "allow",
            "device_filter_patterns": "Kitchen*",
        })

    def test_options_updated(self):
        self.assertEqual(
            self.handler._options,
            {
                "is_default": False,
                "base_refresh_rate": 30,
                "stale_device_timeout": 3,
                "device_filter_mode": "allow",
                "device_filter_patterns": "Kitchen*",
            },
        )


class TestMissingPatternsDefaultsToEmpty(TestCase):
    """An empty optional text field is omitted from the form input."""

    def setUp(self):
        self.handler = SpotcastOptionsFlowHandler()
        self.handler._options = {}

        self.handler.set_device_options({
            "set_default": False,
            "base_refresh_rate": 30,
            "stale_device_timeout": 7,
            "device_filter_mode": "deny",
        })

    def test_patterns_default_to_empty_string(self):
        self.assertEqual(
            self.handler._options["device_filter_patterns"],
            "",
        )
