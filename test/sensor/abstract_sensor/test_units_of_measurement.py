"""Module to test the units_of_measurement property"""

from unittest import TestCase
from unittest.mock import MagicMock

from custom_components.spotcast.sensor.abstract_sensor import SpotcastSensor
from custom_components.spotcast.coordinator import SpotcastCoordinator
from custom_components.spotcast.spotify import SpotifyAccount


class DummySensor(SpotcastSensor):
    UNITS_OF_MEASURE = "foos"

    def _update_from_coordinator(self):
        ...


class TestUnitsMeasurement(TestCase):

    def setUp(self):
        self.coordinator = MagicMock(spec=SpotcastCoordinator)
        self.coordinator.account = MagicMock(spec=SpotifyAccount)
        self.sensor = DummySensor(self.coordinator)

    def test_units_of_measurements_from_contstants(self):
        self.assertEqual(self.sensor.unit_of_measurement, "foos")
