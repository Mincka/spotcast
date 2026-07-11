"""Module to test the async_context_index function"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock

from custom_components.spotcast.services.play_media import (
    async_context_index,
    SpotifyAccount,
    ServiceValidationError,
)


class TestAlbumContext(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.account = MagicMock(spec=SpotifyAccount)
        self.account.async_get_album = AsyncMock(return_value={
            "tracks": {"items": [
                {"uri": "spotify:track:aaa"},
                {"uri": "spotify:track:bbb"},
            ]}
        })
        self.result = await async_context_index(
            self.account,
            "spotify:album:foo",
            "spotify:track:bbb",
        )

    def test_context_and_index_returned(self):
        self.assertEqual(self.result, ("spotify:album:foo", 1))


class TestPlaylistContext(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.account = MagicMock(spec=SpotifyAccount)
        self.account.async_get_playlist_tracks = AsyncMock(return_value=[
            {"track": {"uri": "spotify:track:aaa"}},
            {"track": None},
            {"track": {"uri": "spotify:track:bbb"}},
        ])
        self.result = await async_context_index(
            self.account,
            "spotify:playlist:foo",
            "spotify:track:bbb",
        )

    def test_context_and_index_returned(self):
        self.assertEqual(self.result, ("spotify:playlist:foo", 1))


class TestInvalidContext(IsolatedAsyncioTestCase):

    async def test_unsupported_context_raises(self):
        account = MagicMock(spec=SpotifyAccount)
        with self.assertRaises(ServiceValidationError):
            await async_context_index(
                account,
                "spotify:artist:foo",
                "spotify:track:bbb",
            )

    async def test_track_absent_from_context_raises(self):
        account = MagicMock(spec=SpotifyAccount)
        account.async_get_album = AsyncMock(return_value={
            "tracks": {"items": [{"uri": "spotify:track:aaa"}]}
        })
        with self.assertRaises(ServiceValidationError):
            await async_context_index(
                account,
                "spotify:album:foo",
                "spotify:track:zzz",
            )
