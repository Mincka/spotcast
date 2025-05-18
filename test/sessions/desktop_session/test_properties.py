"""Module to test the token property"""

from unittest import TestCase
from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.spotcast.sessions.desktop_session import DesktopSession


class TestPropertiesRetrieval(TestCase):

    def setUp(self):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
        }

        self.mocks["entry"].data = {
            "desktop_api": {
                "token": {
                    "access_token": "foo",
                    "refresh_token": "bar",
                    "expires_at": 0,
                }
            }
        }

        self.session = DesktopSession(**self.mocks)

    def test_token_value(self):
        self.assertEqual(self.session.token, "foo")

    def test_refresh_token_value(self):
        self.assertEqual(self.session.refresh_token, "bar")

    def test_clean_token_value(self):
        self.assertEqual(self.session.clean_token, self.session.token)

    def test_expires_at_value(self):
        self.assertEqual(self.session.expires_at, 0)
