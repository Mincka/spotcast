"""Module to test the icon_off property"""

from unittest import TestCase
from unittest.mock import MagicMock

from custom_components.spotcast.coordinator import SpotcastCoordinator
from custom_components.spotcast.sensor.abstract_entity import (
    SpotcastEntity,
    SpotifyAccount,
)


class EntityWithoutOffIcon(SpotcastEntity):

    PLATFORM = "dummy"

    @property
    def icon(self):
        ...

    def _update_from_coordinator(self):
        ...


class EntityWithOffIcon(EntityWithoutOffIcon):
    ICON_OFF = "mdi:overwrite"


class TestIconDefinition(TestCase):

    def setUp(self):

        self.mocks = {
            "coordinator": MagicMock(spec=SpotcastCoordinator)
        }

        self.mocks["coordinator"].account = MagicMock(spec=SpotifyAccount)

        self.entities = {
            "with": EntityWithOffIcon(self.mocks["coordinator"]),
            "without": EntityWithoutOffIcon(self.mocks["coordinator"]),
        }

    def test_entity_without_off_icon_returns_icon_with_off_added(self):
        self.assertEqual(self.entities["without"]._icon_off, "mdi:cube-off")

    def test_entity_with_off_icon_returns_overwritten_value(self):
        self.assertEqual(self.entities["with"]._icon_off, "mdi:overwrite")
