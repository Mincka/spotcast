"""Module to test the _update_from_coordinator function"""

from unittest import TestCase
from unittest.mock import MagicMock

from custom_components.spotcast.coordinator import SpotcastCoordinator
from custom_components.spotcast.spotify import SpotifyAccount
from custom_components.spotcast.binary_sensor.is_default_binary_sensor import (
    IsDefaultBinarySensor
)


class TestDataUpdate(TestCase):

    def setUp(self):
        self.coordinator = MagicMock(spec=SpotcastCoordinator)
        self.account = MagicMock(spec=SpotifyAccount)
        self.account.is_default = True
        self.account.entry_id = "1234"
        self.coordinator.account = self.account
        self.sensor = IsDefaultBinarySensor(self.coordinator)
        self.sensor._update_from_coordinator()

    def test_state_set_to_on(self):
        self.assertTrue(self.sensor.is_on)

    def test_sensor_always_available(self):
        self.assertTrue(self.sensor.available)


class TestFailedUpdate(TestCase):

    def setUp(self):
        self.coordinator = MagicMock(spec=SpotcastCoordinator)
        self.account = MagicMock(spec=SpotifyAccount)
        self.account.is_default = True
        self.account.entry_id = "1234"
        self.coordinator.account = self.account
        self.sensor = IsDefaultBinarySensor(self.coordinator)
        self.sensor._handle_update_failure()

    def test_state_still_reported_from_account(self):
        self.assertTrue(self.sensor.is_on)
