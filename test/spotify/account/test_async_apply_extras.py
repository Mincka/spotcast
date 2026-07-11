"""Module to test the async_apply_extras function"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch, AsyncMock
from time import time

from spotipy import SpotifyException

from custom_components.spotcast.spotify.account import (
    SpotifyAccount,
    PublicSession,
    DesktopSession,
    HomeAssistant,
    Store,
)

from test.spotify.account import TEST_MODULE


class TestAppliedExtras(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.Store", spec=Store, new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.Spotify", new_callable=MagicMock)
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

        self.account.async_set_volume = AsyncMock()
        self.account.async_shuffle = AsyncMock()
        self.account.async_repeat = AsyncMock()

        await self.account.async_apply_extras(
            "foo",
            {"volume": 80, "shuffle": True, "repeat": "context"}
        )

    def test_set_volume_was_called(self):
        try:
            self.account.async_set_volume.assert_called_with(80, "foo")
        except AssertionError:
            self.fail()

    def test_shuffle_was_called(self):
        try:
            self.account.async_shuffle.assert_called_with(True, "foo")
        except AssertionError:
            self.fail()

    def test_repeat_was_called(self):
        try:
            self.account.async_repeat.assert_called_with("context", "foo")
        except AssertionError:
            self.fail()


class TestSkippedExtras(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.Store", spec=Store, new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.Spotify", new_callable=MagicMock)
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

        self.account.async_set_volume = AsyncMock()
        self.account.async_shuffle = AsyncMock()
        self.account.async_repeat = AsyncMock()

        await self.account.async_apply_extras(
            "foo",
            {"foo": "bar"}
        )

    def test_set_volume_was_called(self):

        mocks: tuple[AsyncMock] = (
            self.account.async_set_volume,
            self.account.async_shuffle,
            self.account.async_repeat,
        )

        for mock in mocks:
            try:
                mock.assert_not_called()
            except AssertionError:
                self.fail()


class TestApplyExtrasWithException(IsolatedAsyncioTestCase):
    """Test that SpotifyException in extras doesn't crash the call."""

    @patch(f"{TEST_MODULE}.Store", spec=Store, new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.Spotify", new_callable=MagicMock)
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

        # Make volume raise, but shuffle and repeat succeed
        self.account.async_set_volume = AsyncMock(
            side_effect=SpotifyException(403, -1, "Forbidden")
        )
        self.account.async_shuffle = AsyncMock()
        self.account.async_repeat = AsyncMock()

        # Should not raise despite volume failing
        await self.account.async_apply_extras(
            "foo",
            {"volume": 80, "shuffle": True, "repeat": "context"}
        )

    def test_shuffle_still_called_despite_volume_error(self):
        try:
            self.account.async_shuffle.assert_called_with(True, "foo")
        except AssertionError:
            self.fail()

    def test_repeat_still_called_despite_volume_error(self):
        try:
            self.account.async_repeat.assert_called_with("context", "foo")
        except AssertionError:
            self.fail()
