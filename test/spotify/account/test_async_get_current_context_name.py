"""Module to test the async_get_current_context_name function"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock

from custom_components.spotcast.spotify.account import (
    SpotifyAccount,
    PublicSession,
    DesktopSession,
    HomeAssistant,
    Spotify,
    Store,
)

from test.spotify.account import TEST_MODULE


class _AccountCase(IsolatedAsyncioTestCase):

    PLAYBACK = {}

    @patch(
        f"{TEST_MODULE}.internal.async_get_playlist_name",
        new_callable=AsyncMock,
    )
    @patch(f"{TEST_MODULE}.Store", spec=Store, new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.Spotify", spec=Spotify, new_callable=MagicMock)
    async def asyncSetUp(
        self,
        mock_spotify: MagicMock,
        mock_store: MagicMock,
        mock_name: AsyncMock,
    ):
        mock_name.return_value = "Resolved Name"
        self.mock_name = mock_name

        self.account = SpotifyAccount(
            entry_id="12345",
            hass=MagicMock(spec=HomeAssistant),
            public_session=MagicMock(spec=PublicSession),
            private_session=MagicMock(spec=DesktopSession),
            is_default=True,
        )

        self.patcher = patch.object(
            SpotifyAccount,
            "playback_state",
            new_callable=PropertyMock,
            return_value=self.PLAYBACK,
        )
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

        self.result = await self.account.async_get_current_context_name()


class TestPlaylistContext(_AccountCase):

    PLAYBACK = {
        "context": {
            "uri": "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",
            "type": "playlist",
        }
    }

    def test_name_resolved(self):
        self.assertEqual(self.result, "Resolved Name")

    def test_helper_called_with_uri(self):
        try:
            self.mock_name.assert_called_once_with(
                self.account, "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"
            )
        except AssertionError as exc:
            self.fail(exc)


class TestAlbumContext(_AccountCase):

    PLAYBACK = {
        "context": {
            "uri": "spotify:album:1234",
            "type": "album",
        }
    }

    def test_returns_none(self):
        self.assertIsNone(self.result)

    def test_helper_not_called(self):
        try:
            self.mock_name.assert_not_called()
        except AssertionError as exc:
            self.fail(exc)


class TestNoContext(_AccountCase):

    PLAYBACK = {}

    def test_returns_none(self):
        self.assertIsNone(self.result)

    def test_helper_not_called(self):
        try:
            self.mock_name.assert_not_called()
        except AssertionError as exc:
            self.fail(exc)


class TestCachedByUri(IsolatedAsyncioTestCase):
    """A second lookup for the same context uri reuses the cached name
    without hitting the internal endpoint again."""

    @patch(
        f"{TEST_MODULE}.internal.async_get_playlist_name",
        new_callable=AsyncMock,
    )
    @patch(f"{TEST_MODULE}.Store", spec=Store, new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.Spotify", spec=Spotify, new_callable=MagicMock)
    async def asyncSetUp(
        self,
        mock_spotify: MagicMock,
        mock_store: MagicMock,
        mock_name: AsyncMock,
    ):
        mock_name.return_value = "Cached Name"
        self.mock_name = mock_name

        self.account = SpotifyAccount(
            entry_id="12345",
            hass=MagicMock(spec=HomeAssistant),
            public_session=MagicMock(spec=PublicSession),
            private_session=MagicMock(spec=DesktopSession),
            is_default=True,
        )

        playback = {
            "context": {
                "uri": "spotify:playlist:foo",
                "type": "playlist",
            }
        }

        with patch.object(
            SpotifyAccount,
            "playback_state",
            new_callable=PropertyMock,
            return_value=playback,
        ):
            self.first = await self.account.async_get_current_context_name()
            self.second = await self.account.async_get_current_context_name()

    def test_both_return_name(self):
        self.assertEqual(self.first, "Cached Name")
        self.assertEqual(self.second, "Cached Name")

    def test_helper_called_once(self):
        try:
            self.mock_name.assert_called_once()
        except AssertionError as exc:
            self.fail(exc)
