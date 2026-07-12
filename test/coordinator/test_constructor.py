"""Module to test the constructor of the SpotcastCoordinator"""

from datetime import timedelta
from unittest import TestCase
from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.spotcast.coordinator import SpotcastCoordinator
from custom_components.spotcast.spotify import SpotifyAccount


class TestDataRetention(TestCase):

    def setUp(self):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "account": MagicMock(spec=SpotifyAccount),
        }

        self.mocks["entry"].entry_id = "12345"
        self.mocks["account"].base_refresh_rate = 20

        self.coordinator = SpotcastCoordinator(
            self.mocks["hass"],
            self.mocks["entry"],
            self.mocks["account"],
        )

    def test_account_is_retained(self):
        self.assertIs(self.coordinator.account, self.mocks["account"])

    def test_config_entry_is_retained(self):
        self.assertIs(self.coordinator.config_entry, self.mocks["entry"])

    def test_update_interval_based_on_base_refresh_rate(self):
        self.assertEqual(
            self.coordinator.update_interval,
            timedelta(seconds=20),
        )
