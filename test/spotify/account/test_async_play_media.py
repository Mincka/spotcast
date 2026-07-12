"""Module to test the async_play_media function"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch, AsyncMock
from time import time

from custom_components.spotcast.spotify.account import (
    SpotifyAccount,
    PublicSession,
    DesktopSession,
    HomeAssistant,
    PlaybackError,
    SpotifyException,
    Spotify,
    Store,
)

from test.spotify.account import TEST_MODULE


class TestMediaPlayback(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.Store", spec=Store, new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.Spotify", spec=Spotify, new_callable=MagicMock)
    async def asyncSetUp(
            self,
            mock_spotify: MagicMock,
            mock_store: MagicMock,
    ):

        self.mocks = {
            "internal": MagicMock(spec=DesktopSession),
            "external": MagicMock(spec=PublicSession),
            "hass": MagicMock(spec=HomeAssistant),
        }
        self.mocks["hass"].loop = MagicMock()

        self.mock_spotify = mock_spotify

        self.mocks["external"].token = {
            "access_token": "12345",
            "expires_at": 12345.61,
        }

        self.account = SpotifyAccount(
            entry_id="12345",
            hass=self.mocks["hass"],
            public_session=self.mocks["external"],
            private_session=self.mocks["internal"],
            is_default=True
        )

        self.account.async_ensure_tokens_valid = AsyncMock()

        self.account._datasets["profile"].expires_at = time() + 9999
        self.account._datasets["profile"]._data = {"name": "Dummy"}

        self.mocks["hass"].async_add_executor_job = AsyncMock()

        await self.account.async_play_media(
            "foo",
            "spotify:dummy:uri"
        )

    def test_play_media_was_called(self):
        try:
            self.mocks["hass"].async_add_executor_job.assert_called_with(
                self.account.apis["public"].start_playback,
                "foo",
                "spotify:dummy:uri",
                None,
                None,
                None,
            )
        except AssertionError:
            self.fail()


class TestEmptyContext(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.Store", spec=Store, new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.Spotify", spec=Spotify, new_callable=MagicMock)
    async def asyncSetUp(
            self,
            mock_spotify: MagicMock,
            mock_store: MagicMock,
    ):

        self.mocks = {
            "internal": MagicMock(spec=DesktopSession),
            "external": MagicMock(spec=PublicSession),
            "hass": MagicMock(spec=HomeAssistant),
        }
        self.mocks["hass"].loop = MagicMock()

        self.mock_spotify = mock_spotify

        self.mocks["external"].token = {
            "access_token": "12345",
            "expires_at": 12345.61,
        }

        self.account = SpotifyAccount(
            entry_id="12345",
            hass=self.mocks["hass"],
            public_session=self.mocks["external"],
            private_session=self.mocks["internal"],
            is_default=True
        )

        self.account.async_ensure_tokens_valid = AsyncMock()

        self.account._datasets["profile"].expires_at = time() + 9999
        self.account._datasets["profile"]._data = {"name": "Dummy"}

        self.mocks["hass"].async_add_executor_job = AsyncMock()

        await self.account.async_play_media("foo")

    def test_play_media_was_called(self):
        try:
            self.mocks["hass"].async_add_executor_job.assert_called_with(
                self.account.apis["public"].transfer_playback,
                "foo",
                True
            )
        except AssertionError:
            self.fail()


class TestFailedTransfer(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.Store", spec=Store, new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.Spotify", spec=Spotify, new_callable=MagicMock)
    async def asyncSetUp(
            self,
            mock_spotify: MagicMock,
            mock_store: MagicMock,
    ):

        self.mocks = {
            "internal": MagicMock(spec=DesktopSession),
            "external": MagicMock(spec=PublicSession),
            "hass": MagicMock(spec=HomeAssistant),
        }
        self.mocks["hass"].loop = MagicMock()

        self.mock_spotify = mock_spotify

        self.mocks["external"].token = {
            "access_token": "12345",
            "expires_at": 12345.61,
        }

        self.account = SpotifyAccount(
            entry_id="12345",
            hass=self.mocks["hass"],
            public_session=self.mocks["external"],
            private_session=self.mocks["internal"],
            is_default=True
        )

        self.account.async_ensure_tokens_valid = AsyncMock()

        self.account._datasets["profile"].expires_at = time() + 9999
        self.account._datasets["profile"]._data = {"name": "Dummy"}

        self.mocks["hass"].async_add_executor_job = AsyncMock(
            side_effect=SpotifyException(403, "foo", "bar")
        )

        with self.assertRaises(PlaybackError):
            await self.account.async_play_media("foo")

    def test_play_media_was_called(self):
        try:
            self.mocks["hass"].async_add_executor_job.assert_called_with(
                self.account.apis["public"].transfer_playback,
                "foo",
                True
            )
        except AssertionError:
            self.fail()


class TestMediaPlaybackWithExtras(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.Store", spec=Store, new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.Spotify", spec=Spotify, new_callable=MagicMock)
    async def asyncSetUp(
            self,
            mock_spotify: MagicMock,
            mock_store: MagicMock,
    ):

        self.mocks = {
            "internal": MagicMock(spec=DesktopSession),
            "external": MagicMock(spec=PublicSession),
            "hass": MagicMock(spec=HomeAssistant),
        }
        self.mocks["hass"].loop = MagicMock()

        self.mock_spotify = mock_spotify

        self.mocks["external"].token = {
            "access_token": "12345",
            "expires_at": 12345.61,
        }

        self.account = SpotifyAccount(
            entry_id="12345",
            hass=self.mocks["hass"],
            public_session=self.mocks["external"],
            private_session=self.mocks["internal"],
            is_default=True
        )

        self.account.async_ensure_tokens_valid = AsyncMock()

        self.account._datasets["profile"].expires_at = time() + 9999
        self.account._datasets["profile"]._data = {"name": "Dummy"}

        self.mocks["hass"].async_add_executor_job = AsyncMock()

        await self.account.async_play_media(
            "foo",
            "spotify:dummy:uri",
            offset=2,
            position=2.5346,
        )

    def test_play_media_was_called(self):
        try:
            self.mocks["hass"].async_add_executor_job.assert_called_with(
                self.account.apis["public"].start_playback,
                "foo",
                "spotify:dummy:uri",
                None,
                {"position": 2},
                2534,
            )
        except AssertionError:
            self.fail()


class TestMediaPlaybackWithUriOffset(IsolatedAsyncioTestCase):
    """A string offset is a track uri and must be passed to Spotify as a
    uri-based offset, so playback starts at that track without resolving
    its numeric position (see #582)."""

    @patch(f"{TEST_MODULE}.Store", spec=Store, new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.Spotify", spec=Spotify, new_callable=MagicMock)
    async def asyncSetUp(
            self,
            mock_spotify: MagicMock,
            mock_store: MagicMock,
    ):

        self.mocks = {
            "internal": MagicMock(spec=DesktopSession),
            "external": MagicMock(spec=PublicSession),
            "hass": MagicMock(spec=HomeAssistant),
        }
        self.mocks["hass"].loop = MagicMock()

        self.mock_spotify = mock_spotify

        self.mocks["external"].token = {
            "access_token": "12345",
            "expires_at": 12345.61,
        }

        self.account = SpotifyAccount(
            entry_id="12345",
            hass=self.mocks["hass"],
            public_session=self.mocks["external"],
            private_session=self.mocks["internal"],
            is_default=True
        )

        self.account.async_ensure_tokens_valid = AsyncMock()

        self.account._datasets["profile"].expires_at = time() + 9999
        self.account._datasets["profile"]._data = {"name": "Dummy"}

        self.mocks["hass"].async_add_executor_job = AsyncMock()

        await self.account.async_play_media(
            "foo",
            "spotify:playlist:uri",
            offset="spotify:track:bar",
        )

    def test_play_media_was_called(self):
        try:
            self.mocks["hass"].async_add_executor_job.assert_called_with(
                self.account.apis["public"].start_playback,
                "foo",
                "spotify:playlist:uri",
                None,
                {"uri": "spotify:track:bar"},
                None,
            )
        except AssertionError:
            self.fail()


class TestDeviceNotReadyThenSucceeds(IsolatedAsyncioTestCase):
    """A device that is not registered yet answers 404 on the first play
    attempt. Spotcast waits for it and retries once, so playback starts
    without surfacing an error (see #572)."""

    @patch(f"{TEST_MODULE}.Store", spec=Store, new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.Spotify", spec=Spotify, new_callable=MagicMock)
    async def asyncSetUp(
            self,
            mock_spotify: MagicMock,
            mock_store: MagicMock,
    ):

        self.mocks = {
            "internal": MagicMock(spec=DesktopSession),
            "external": MagicMock(spec=PublicSession),
            "hass": MagicMock(spec=HomeAssistant),
        }
        self.mocks["hass"].loop = MagicMock()

        self.mocks["external"].token = {
            "access_token": "12345",
            "expires_at": 12345.61,
        }

        self.account = SpotifyAccount(
            entry_id="12345",
            hass=self.mocks["hass"],
            public_session=self.mocks["external"],
            private_session=self.mocks["internal"],
            is_default=True
        )

        self.account.async_ensure_tokens_valid = AsyncMock()
        self.account.async_wait_for_device = AsyncMock()

        self.account._datasets["profile"].expires_at = time() + 9999
        self.account._datasets["profile"]._data = {"name": "Dummy"}

        self.mocks["hass"].async_add_executor_job = AsyncMock(
            side_effect=[
                SpotifyException(404, -1, "Device not found"),
                None,
            ]
        )

        await self.account.async_play_media("foo", "spotify:dummy:uri")

    def test_waited_for_device(self):
        try:
            self.account.async_wait_for_device.assert_called_once_with("foo")
        except AssertionError:
            self.fail()

    def test_play_retried(self):
        self.assertEqual(
            self.mocks["hass"].async_add_executor_job.call_count,
            2,
        )


class TestDeviceNeverAvailable(IsolatedAsyncioTestCase):
    """When the device never becomes available, waiting times out and a
    clear PlaybackError is raised (see #572)."""

    @patch(f"{TEST_MODULE}.Store", spec=Store, new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.Spotify", spec=Spotify, new_callable=MagicMock)
    async def test_error_raised(
            self,
            mock_spotify: MagicMock,
            mock_store: MagicMock,
    ):

        self.mocks = {
            "internal": MagicMock(spec=DesktopSession),
            "external": MagicMock(spec=PublicSession),
            "hass": MagicMock(spec=HomeAssistant),
        }
        self.mocks["hass"].loop = MagicMock()

        self.mocks["external"].token = {
            "access_token": "12345",
            "expires_at": 12345.61,
        }

        self.account = SpotifyAccount(
            entry_id="12345",
            hass=self.mocks["hass"],
            public_session=self.mocks["external"],
            private_session=self.mocks["internal"],
            is_default=True
        )

        self.account.async_ensure_tokens_valid = AsyncMock()
        self.account.async_wait_for_device = AsyncMock(
            side_effect=TimeoutError()
        )

        self.account._datasets["profile"].expires_at = time() + 9999
        self.account._datasets["profile"]._data = {"name": "Dummy"}

        self.mocks["hass"].async_add_executor_job = AsyncMock(
            side_effect=SpotifyException(404, -1, "Device not found")
        )

        with self.assertRaises(PlaybackError):
            await self.account.async_play_media("foo", "spotify:dummy:uri")


class TestPlaybackError(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.Store", spec=Store, new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.Spotify", spec=Spotify, new_callable=MagicMock)
    async def test_error_raised(
            self,
            mock_spotify: MagicMock,
            mock_store: MagicMock,
    ):

        self.mocks = {
            "internal": MagicMock(spec=DesktopSession),
            "external": MagicMock(spec=PublicSession),
            "hass": MagicMock(spec=HomeAssistant),
        }
        self.mocks["hass"].loop = MagicMock()

        self.mock_spotify = mock_spotify

        self.mocks["external"].token = {
            "access_token": "12345",
            "expires_at": 12345.61,
        }

        self.account = SpotifyAccount(
            entry_id="12345",
            hass=self.mocks["hass"],
            public_session=self.mocks["external"],
            private_session=self.mocks["internal"],
            is_default=True
        )

        self.account.async_ensure_tokens_valid = AsyncMock()

        self.account._datasets["profile"].expires_at = time() + 9999
        self.account._datasets["profile"]._data = {"name": "Dummy"}

        self.mocks["hass"].async_add_executor_job = AsyncMock()
        self.mocks["hass"].async_add_executor_job\
            .side_effect = SpotifyException(MagicMock(), 418, "I'm a teapot'")

        with self.assertRaises(PlaybackError):
            await self.account.async_play_media(
                "foo",
                "spotify:dummy:uri"
            )
