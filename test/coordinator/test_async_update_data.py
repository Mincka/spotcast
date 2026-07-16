"""Module to test the _async_update_data function"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import UpdateFailed
from spotipy import SpotifyException
from urllib3.exceptions import ReadTimeoutError

from custom_components.spotcast.coordinator import SpotcastCoordinator
from custom_components.spotcast.media_player.device_manager import (
    DeviceManager,
)
from custom_components.spotcast.spotify import SpotifyAccount


class TestSuccessfulUpdate(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "account": MagicMock(spec=SpotifyAccount),
            "device_manager": MagicMock(spec=DeviceManager),
        }

        self.mocks["entry"].entry_id = "12345"
        self.mocks["account"].entry_id = "12345"
        self.mocks["account"].base_refresh_rate = 30

        self.mocks["account"].async_profile\
            .return_value = {"id": "dummy_id"}
        self.mocks["account"].async_devices\
            .return_value = [{"id": "device"}]
        self.mocks["account"].async_playback_state\
            .return_value = {"device": {"id": "device"}}
        self.mocks["account"].async_playlists_count.return_value = 10
        self.mocks["account"].async_liked_songs_count.return_value = 5
        self.mocks["account"].async_get_current_context_name\
            .return_value = "My Playlist"

        self.mocks["device_manager"].async_update = AsyncMock()

        self.mocks["hass"].data = {
            "spotcast": {
                "12345": {
                    "account": self.mocks["account"],
                    "device_manager": self.mocks["device_manager"],
                }
            }
        }

        self.coordinator = SpotcastCoordinator(
            self.mocks["hass"],
            self.mocks["entry"],
            self.mocks["account"],
        )

        self.result = await self.coordinator._async_update_data()

    def test_data_returned(self):
        self.assertEqual(
            self.result,
            {
                "profile": {"id": "dummy_id"},
                "devices": [{"id": "device"}],
                "playback_state": {"device": {"id": "device"}},
                "playlists_count": 10,
                "liked_songs_count": 5,
                "context_name": "My Playlist",
            },
        )

    def test_profile_was_refreshed(self):
        try:
            self.mocks["account"].async_profile.assert_awaited()
        except AssertionError:
            self.fail()

    def test_devices_were_refreshed(self):
        try:
            self.mocks["account"].async_devices.assert_awaited()
        except AssertionError:
            self.fail()

    def test_playback_state_was_refreshed(self):
        try:
            self.mocks["account"].async_playback_state.assert_awaited()
        except AssertionError:
            self.fail()

    def test_device_manager_was_updated(self):
        try:
            self.mocks["device_manager"].async_update.assert_awaited_once()
        except AssertionError:
            self.fail()


class TestUpdateWithoutDeviceManager(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "account": MagicMock(spec=SpotifyAccount),
        }

        self.mocks["entry"].entry_id = "12345"
        self.mocks["account"].entry_id = "12345"
        self.mocks["account"].base_refresh_rate = 30

        self.mocks["account"].async_profile\
            .return_value = {"id": "dummy_id"}
        self.mocks["account"].async_devices.return_value = []
        self.mocks["account"].async_playback_state.return_value = {}
        self.mocks["account"].async_playlists_count.return_value = 0
        self.mocks["account"].async_liked_songs_count.return_value = 0

        self.mocks["hass"].data = {}

        self.coordinator = SpotcastCoordinator(
            self.mocks["hass"],
            self.mocks["entry"],
            self.mocks["account"],
        )

        self.result = await self.coordinator._async_update_data()

    def test_data_returned(self):
        self.assertEqual(self.result["profile"], {"id": "dummy_id"})


class TestFailedUpdate(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "account": MagicMock(spec=SpotifyAccount),
        }

        self.mocks["entry"].entry_id = "12345"
        self.mocks["account"].entry_id = "12345"
        self.mocks["account"].base_refresh_rate = 30

        self.mocks["account"].async_profile.side_effect = ReadTimeoutError(
            MagicMock(),
            MagicMock(),
            MagicMock(),
        )

        self.mocks["hass"].data = {}

        self.coordinator = SpotcastCoordinator(
            self.mocks["hass"],
            self.mocks["entry"],
            self.mocks["account"],
        )

    async def test_update_failed_raised(self):
        with self.assertRaises(UpdateFailed):
            await self.coordinator._async_update_data()


class TestRetryExhaustedServerErrors(IsolatedAsyncioTestCase):
    """spotipy reports retry exhaustion as a 429 even when the retried
    responses were 5xx server errors. The coordinator must report those
    as a Spotify outage, not a rate limit."""

    async def asyncSetUp(self):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "account": MagicMock(spec=SpotifyAccount),
        }

        self.mocks["entry"].entry_id = "12345"
        self.mocks["account"].entry_id = "12345"
        self.mocks["account"].base_refresh_rate = 30

        self.mocks["account"].async_profile.side_effect = SpotifyException(
            429,
            -1,
            "/v1/me/playlists?limit=1&offset=0:\n Max Retries",
            reason="too many 502 error responses",
        )

        self.mocks["hass"].data = {}

        self.coordinator = SpotcastCoordinator(
            self.mocks["hass"],
            self.mocks["entry"],
            self.mocks["account"],
        )

    async def test_reported_as_server_outage(self):
        with self.assertRaises(UpdateFailed) as context:
            await self.coordinator._async_update_data()

        self.assertIn(
            "Spotify API temporarily unavailable",
            str(context.exception),
        )

    async def test_misleading_rate_limit_status_not_reported(self):
        with self.assertRaises(UpdateFailed) as context:
            await self.coordinator._async_update_data()

        self.assertNotIn("429", str(context.exception))


class TestRetryExhaustedRateLimit(IsolatedAsyncioTestCase):
    """A genuine rate limit exhaustion keeps the default message."""

    async def asyncSetUp(self):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "account": MagicMock(spec=SpotifyAccount),
        }

        self.mocks["entry"].entry_id = "12345"
        self.mocks["account"].entry_id = "12345"
        self.mocks["account"].base_refresh_rate = 30

        self.mocks["account"].async_profile.side_effect = SpotifyException(
            429,
            -1,
            "/v1/me/playlists?limit=1&offset=0:\n Max Retries",
            reason="too many 429 error responses",
        )

        self.mocks["hass"].data = {}

        self.coordinator = SpotcastCoordinator(
            self.mocks["hass"],
            self.mocks["entry"],
            self.mocks["account"],
        )

    async def test_default_message_kept(self):
        with self.assertRaises(UpdateFailed) as context:
            await self.coordinator._async_update_data()

        self.assertIn(
            "Could not refresh Spotify data for entry `12345`",
            str(context.exception),
        )
