"""Module to test the can_convert."""

from unittest import TestCase
from unittest.mock import MagicMock

from custom_components.spotcast.config_flow_classes.config_flow_handler import (
    SpotcastFlowHandler,
)


class TestCanConvert(TestCase):

    def setUp(self):
        SpotcastFlowHandler.ALLOWED_CONVERT = ["2.*", "1.2"]

    def test_specific_version(self):
        self.assertTrue(SpotcastFlowHandler.can_convert("1.2"))

    def test_major_blob(self):
        self.assertTrue(SpotcastFlowHandler.can_convert("2.2"))


class TestCannotConvert(TestCase):

    def setUp(self):
        SpotcastFlowHandler.ALLOWED_CONVERT = ["2.*", "1.2"]

    def test_specific_version(self):
        self.assertFalse(SpotcastFlowHandler.can_convert("1.5"))
