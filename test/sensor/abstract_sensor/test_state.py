"""Module to test the state property"""

from unittest import TestCase
from unittest.mock import MagicMock

from custom_components.spotcast.sensor.abstract_sensor import SpotcastSensor
from custom_components.spotcast.coordinator import SpotcastCoordinator
from custom_components.spotcast.spotify import SpotifyAccount


class DummySensor(SpotcastSensor):
    UNITS_OF_MEASURE = "foos"

    def _update_from_coordinator(self):
        ...


class TestSensorState(TestCase):

    def setUp(self):
        self.coordinator = MagicMock(spec=SpotcastCoordinator)
        self.coordinator.account = MagicMock(spec=SpotifyAccount)
        self.sensor = DummySensor(self.coordinator)
        self.sensor._attr_state = 10

    def test_sensor_state_returned(self):
        self.assertEqual(self.sensor.state, 10)
