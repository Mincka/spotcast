"""Module to test the async_setup_entry function"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from custom_components.spotcast.media_player import (
    async_setup_entry,
    SpotifyAccount,
    HomeAssistant,
    ConfigEntry,
    AddEntitiesCallback,
    DeviceManager,
)

TEST_MODULE = "custom_components.spotcast.media_player"


class TestMediaPlayerSetup(IsolatedAsyncioTestCase):

    @patch.object(DeviceManager, "async_initialize")
    @patch.object(DeviceManager, "async_update")
    @patch.object(
        SpotifyAccount,
        "async_from_config_entry",
        return_value=MagicMock(spec=SpotifyAccount)
    )
    async def asyncSetUp(
        self,
        mock_account: AsyncMock,
        mock_update: AsyncMock,
        mock_initialize: AsyncMock,
    ):

        self.mock_update = mock_update
        self.mock_initialize = mock_initialize

        self.mock_hass = MagicMock(spec=HomeAssistant)
        self.mock_entry = MagicMock(spec=ConfigEntry)
        self.mock_callback = MagicMock(spec=AddEntitiesCallback)
        self.mock_entry.entry_id = "12345"
        self.mock_entry.options = {}
        self.mock_hass.data = {}

        await async_setup_entry(
            self.mock_hass,
            self.mock_entry,
            self.mock_callback,
        )

    async def test_update_called(self):
        try:
            self.mock_update.assert_called()
        except AssertionError:
            self.fail()

    async def test_initialize_called(self):
        try:
            self.mock_initialize.assert_called()
        except AssertionError:
            self.fail()

    async def test_device_manager_stored_in_hass_data(self):
        device_manager = self.mock_hass            .data["spotcast"]["12345"]["device_manager"]
        self.assertIsInstance(device_manager, DeviceManager)
