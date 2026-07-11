"""Module to test the async_setup_entry"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock

from custom_components.spotcast.coordinator import SpotcastCoordinator
from custom_components.spotcast.spotify import SpotifyAccount
from custom_components.spotcast.binary_sensor import (
    async_setup_entry,
    HomeAssistant,
    ConfigEntry,
    AddEntitiesCallback,
)


class TestSetupEntry(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "coordinator": MagicMock(spec=SpotcastCoordinator),
            "account": MagicMock(spec=SpotifyAccount),
            "add_entities": MagicMock(spec=AddEntitiesCallback),
        }

        self.mocks["account"].id = "dummy_account"
        self.mocks["coordinator"].account = self.mocks["account"]

        self.mocks["entry"].entry_id = "12345"
        self.mocks["hass"].data = {
            "spotcast": {
                "12345": {
                    "account": self.mocks["account"],
                    "coordinator": self.mocks["coordinator"],
                }
            }
        }

        await async_setup_entry(
            self.mocks["hass"],
            self.mocks["entry"],
            self.mocks["add_entities"],
        )

    def test_async_add_entities_was_called(self):
        try:
            self.mocks["add_entities"].assert_called()
        except AssertionError:
            self.fail()
