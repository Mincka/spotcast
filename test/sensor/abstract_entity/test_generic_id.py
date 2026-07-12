"""Module to test the _generic_id property"""

from unittest import TestCase
from unittest.mock import MagicMock

from custom_components.spotcast.coordinator import SpotcastCoordinator
from custom_components.spotcast.sensor.abstract_entity import (
    SpotcastEntity,
    SpotifyAccount,
)


class EntityWithoutId(SpotcastEntity):

    PLATFORM = "dummy"
    GENERIC_NAME = "Entity Class"

    @property
    def icon(self):
        ...

    def _update_from_coordinator(self):
        ...


class EntityWithId(EntityWithoutId):
    GENERIC_ID = "overwrite"


class TestGenericIdDefinition(TestCase):

    def setUp(self):
        self.mocks = {
            "coordinator": MagicMock(spec=SpotcastCoordinator)
        }

        self.mocks["coordinator"].account = MagicMock(spec=SpotifyAccount)

        self.entities = {
            "with_id": EntityWithId(self.mocks["coordinator"]),
            "without_id": EntityWithoutId(self.mocks["coordinator"]),
        }

    def test_entity_without_id(self):
        self.assertEqual(
            self.entities["without_id"]._generic_id,
            "entity_class"
        )

    def test_entity_with_id(self):
        self.assertEqual(
            self.entities["with_id"]._generic_id,
            "overwrite"
        )
