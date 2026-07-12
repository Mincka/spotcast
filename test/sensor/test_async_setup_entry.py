"""Module to test the async_setup_entry function"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock

from custom_components.spotcast.coordinator import SpotcastCoordinator
from custom_components.spotcast.spotify import SpotifyAccount
from custom_components.spotcast.sensor import (
    async_setup_entry,
    HomeAssistant,
    ConfigEntry,
    AddEntitiesCallback,
    SENSORS,
)


class TestSensorCreation(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "add_entities": MagicMock(spec=AddEntitiesCallback),
            "coordinator": MagicMock(spec=SpotcastCoordinator),
            "account": MagicMock(spec=SpotifyAccount),
        }

        self.mocks["account"].id = "dummy_account"
        self.mocks["account"].product = "free"
        self.mocks["coordinator"].account = self.mocks["account"]

        self.mocks["hass"].data = {
            "spotcast": {
                "12345": {
                    "account": self.mocks["account"],
                    "coordinator": self.mocks["coordinator"],
                }
            }
        }

        self.mocks["entry"].entry_id = "12345"

        await async_setup_entry(
            self.mocks["hass"],
            self.mocks["entry"],
            self.mocks["add_entities"]
        )

    def test_add_entity_was_called(self):
        try:
            self.mocks["add_entities"].assert_called()
        except AssertionError:
            self.fail()

    def test_all_sensors_created(self):
        entities = self.mocks["add_entities"].call_args.args[0]
        self.assertEqual(len(entities), len(SENSORS))

    def test_sensors_built_with_coordinator(self):
        entities = self.mocks["add_entities"].call_args.args[0]

        for entity in entities:
            self.assertIs(entity.coordinator, self.mocks["coordinator"])
