"""Module to test the _update_from_coordinator function"""

from unittest import TestCase
from unittest.mock import MagicMock

from custom_components.spotcast.coordinator import SpotcastCoordinator
from custom_components.spotcast.spotify import SpotifyAccount
from custom_components.spotcast.sensor.spotify_devices_sensor import (
    SpotifyDevicesSensor,
)


class TestSuccessfulUpdate(TestCase):

    def setUp(self):

        self.coordinator = MagicMock(spec=SpotcastCoordinator)
        self.coordinator.account = MagicMock(spec=SpotifyAccount)
        self.coordinator.account.name = "Dummy Account"
        self.coordinator.data = {"devices": ["foo", "bar"]}

        self.sensor = SpotifyDevicesSensor(self.coordinator)
        self.sensor._update_from_coordinator()

    def test_attribute_state_was_set_to_device_count(self):
        self.assertEqual(self.sensor.state, 2)

    def test_extra_attributes_properly_set(self):
        self.assertEqual(
            self.sensor.extra_state_attributes,
            {"devices": ["foo", "bar"]}
        )
