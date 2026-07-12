"""Module to test the coordinator update handling of the sensor"""

from unittest import TestCase
from unittest.mock import MagicMock

from custom_components.spotcast.coordinator import SpotcastCoordinator
from custom_components.spotcast.spotify import SpotifyAccount
from custom_components.spotcast.binary_sensor    .spotify_profile_malfunction_sensor import (
        SpotifyProfileMalfunctionBinarySensor,
    )


class TestSuccessfulUpdate(TestCase):

    def setUp(self):
        self.coordinator = MagicMock(spec=SpotcastCoordinator)
        self.account = MagicMock(spec=SpotifyAccount)
        self.account.is_default = True
        self.account.entry_id = "1234"
        self.coordinator.account = self.account
        self.sensor = SpotifyProfileMalfunctionBinarySensor(self.coordinator)
        self.sensor._update_from_coordinator()

    def test_state_set_to_off(self):
        self.assertFalse(self.sensor.is_on)


class TestUnsuccessfulUpdate(TestCase):

    def setUp(self):
        self.coordinator = MagicMock(spec=SpotcastCoordinator)
        self.account = MagicMock(spec=SpotifyAccount)
        self.account.is_default = True
        self.account.entry_id = "1234"
        self.coordinator.account = self.account
        self.coordinator.last_exception = Exception("Dummy Error")
        self.sensor = SpotifyProfileMalfunctionBinarySensor(self.coordinator)
        self.sensor._handle_update_failure()

    def test_state_set_to_on(self):
        self.assertTrue(self.sensor.is_on)

    def test_sensor_remains_available(self):
        self.assertTrue(self.sensor.available)
