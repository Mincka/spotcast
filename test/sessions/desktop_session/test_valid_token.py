"""Module to test the valid_token property"""

from time import time
from unittest import TestCase
from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.spotcast.sessions.desktop_session import DesktopSession


class TestValidToken(TestCase):

    def setUp(self):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
        }

        self.mocks["entry"].data = {
            "desktop_api": {
                "token": {
                    "expires_at": time() + 9999
                }
            }
        }

        self.session = DesktopSession(**self.mocks)

    def test_token_is_valid(self):
        self.assertTrue(self.session.valid_token)


class TestInvalidToken(TestCase):

    def setUp(self):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
        }

        self.mocks["entry"].data = {
            "desktop_api": {
                "token": {
                    "expires_at": 0
                }
            }
        }

        self.session = DesktopSession(**self.mocks)

    def test_token_is_valid(self):
        self.assertFalse(self.session.valid_token)
