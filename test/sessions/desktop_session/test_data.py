"""Module to test the data property"""

from unittest import TestCase
from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.spotcast.sessions.desktop_session import DesktopSession


class TestDataValues(TestCase):

    def setUp(self):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
        }

        self.mocks["entry"].data = {
            "desktop_api": {
                "token": {
                    "foo": "bar"
                }
            }
        }

        self.session = DesktopSession(self.mocks["hass"], self.mocks["entry"])
        self.result = self.session._data

    def test_data_content(self):
        self.assertEqual(self.result, {"token": {"foo": "bar"}})
