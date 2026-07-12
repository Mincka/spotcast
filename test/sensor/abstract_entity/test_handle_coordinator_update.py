"""Module to test the _handle_coordinator_update function"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from custom_components.spotcast.coordinator import SpotcastCoordinator
from custom_components.spotcast.sensor.abstract_entity import (
    SpotcastEntity,
    EntityCategory,
    SpotifyAccount,
    STATE_UNKNOWN,
)


class DummyEntity(SpotcastEntity):

    PLATFORM = "dummy"
    ENTITY_CATEGORY = EntityCategory.CONFIG

    @property
    def _default_attributes(self):
        return {"foo": []}

    @property
    def icon(self):
        """Unimplemented icon property"""

    def _update_from_coordinator(self):
        """Unimplemented _update_from_coordinator"""


class TestSuccessfulUpdate(TestCase):

    @patch.object(DummyEntity, "async_write_ha_state")
    @patch.object(DummyEntity, "_update_from_coordinator")
    def setUp(self, mock_update: MagicMock, mock_write: MagicMock):

        self.mocks = {
            "update": mock_update,
            "write": mock_write,
            "coordinator": MagicMock(spec=SpotcastCoordinator),
        }

        self.mocks["coordinator"].account = MagicMock(spec=SpotifyAccount)
        self.mocks["coordinator"].last_update_success = True

        self.entity = DummyEntity(self.mocks["coordinator"])
        self.entity._attr_state = "FOO"
        self.entity._handle_coordinator_update()

    def test_update_from_coordinator_called(self):
        try:
            self.mocks["update"].assert_called_once()
        except AssertionError:
            self.fail()

    def test_state_unchanged(self):
        self.assertEqual(self.entity._attr_state, "FOO")

    def test_state_written(self):
        try:
            self.mocks["write"].assert_called_once()
        except AssertionError:
            self.fail()


class TestFailedUpdate(TestCase):

    @patch.object(DummyEntity, "async_write_ha_state")
    @patch.object(DummyEntity, "_update_from_coordinator")
    def setUp(self, mock_update: MagicMock, mock_write: MagicMock):

        self.mocks = {
            "update": mock_update,
            "write": mock_write,
            "coordinator": MagicMock(spec=SpotcastCoordinator),
        }

        self.mocks["coordinator"].account = MagicMock(spec=SpotifyAccount)
        self.mocks["coordinator"].last_update_success = False

        self.entity = DummyEntity(self.mocks["coordinator"])
        self.entity._attr_state = "FOO"
        self.entity._attributes = {"foo": [1, 2, 3]}
        self.entity._handle_coordinator_update()

    def test_update_from_coordinator_not_called(self):
        try:
            self.mocks["update"].assert_not_called()
        except AssertionError:
            self.fail()

    def test_state_changed_to_unknown(self):
        self.assertEqual(self.entity._attr_state, STATE_UNKNOWN)

    def test_attributes_resetted(self):
        self.assertEqual(self.entity._attributes, {"foo": []})
