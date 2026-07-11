"""Module to test the name property"""

from unittest import TestCase
from unittest.mock import MagicMock

from custom_components.spotcast.coordinator import SpotcastCoordinator
from custom_components.spotcast.sensor.abstract_entity import (
    SpotcastEntity,
    SpotifyAccount,
)


class DummyEntity(SpotcastEntity):
    PLATFORM = "dummy"

    @property
    def icon(self):
        ...

    def _update_from_coordinator(self):
        ...


class TestNameDefinition(TestCase):

    def setUp(self):
        self.coordinator = MagicMock(spec=SpotcastCoordinator)
        self.account = MagicMock(spec=SpotifyAccount)
        self.account.name = "Dummy Account"
        self.account.id = "dummy_id"
        self.coordinator.account = self.account
        self.entity = DummyEntity(self.coordinator)

    def test_name_value_is_as_expected(self):
        self.assertEqual(
            self.entity.unique_id,
            "dummy.dummy_id_abstract_spotcast"
        )
