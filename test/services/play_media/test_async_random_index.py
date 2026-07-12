"""Module to test the get_ranom_index function"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from spotipy import SpotifyException

from custom_components.spotcast.services.play_media import (
    async_random_index,
    SpotifyAccount,
    ServiceValidationError,
    _RANDOM_FALLBACK_ITEMS,
)

TEST_MODULE = "custom_components.spotcast.services.play_media"


class TestAlbumRandInt(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.randint", new_callable=MagicMock)
    async def asyncSetUp(self, mock_random: MagicMock):

        mock_random.return_value = 5

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount)
        }

        self.mocks["account"].async_get_album = AsyncMock()
        self.mocks["account"].async_get_album.return_value = {
            "total_tracks": 10
        }

        self.resut = await async_random_index(
            self.mocks["account"],
            "spotify:album:foo",
        )

    def test_received_expected_index(self):
        self.assertEqual(self.resut, 5)

    def test_get_album_called(self):
        try:
            self.mocks["account"].async_get_album.assert_called()
        except AssertionError:
            self.fail()


class TestPlaylistRandInt(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.randint", new_callable=MagicMock)
    async def asyncSetUp(self, mock_random: MagicMock):

        mock_random.return_value = 42

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount)
        }

        self.mocks["account"].async_get_playlist = AsyncMock()
        self.mocks["account"].async_get_playlist.return_value = {
            "tracks": {
                "total": 50
            }
        }
        self.resut = await async_random_index(
            self.mocks["account"],
            "spotify:playlist:foo",
        )

    def test_received_expected_index(self):
        self.assertEqual(self.resut, 42)

    def test_get_artist_called(self):
        try:
            self.mocks["account"].async_get_playlist.assert_called()
        except AssertionError:
            self.fail()


class TestUserLikedSongs(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.randint", new_callable=MagicMock)
    async def asyncSetUp(self, mock_random: MagicMock):

        mock_random.return_value = 314

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount)
        }

        self.mocks["account"].async_liked_songs_count = AsyncMock()
        self.mocks["account"].liked_songs_uri = "spotify:user:foo:collection"
        self.mocks["account"].async_liked_songs_count.return_value = 500
        self.resut = await async_random_index(
            self.mocks["account"],
            "spotify:user:foo:collection",
        )

    def test_received_expected_index(self):
        self.assertEqual(self.resut, 314)

    def test_get_artist_called(self):
        try:
            self.mocks["account"].async_liked_songs_count.assert_called()
        except AssertionError:
            self.fail()


class TestInvalidContextUri(IsolatedAsyncioTestCase):

    async def test_error_raised(self):

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount)
        }

        with self.assertRaises(ServiceValidationError):
            self.resut = await async_random_index(
                self.mocks["account"],
                "spotify:track:foo",
            )


class TestPlaylistNotFound(IsolatedAsyncioTestCase):
    """Spotify 404s on its own editorial/algorithmic playlists when
    fetched through the Web API. Random start must fall back to a pseudo-
    random offset within the first `_RANDOM_FALLBACK_ITEMS` tracks instead
    of raising. See issues #570 and #599."""

    @patch(f"{TEST_MODULE}.randint", new_callable=MagicMock)
    async def asyncSetUp(self, mock_random: MagicMock):

        mock_random.return_value = 7

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount),
            "random": mock_random,
        }

        self.mocks["account"].async_get_playlist = AsyncMock(
            side_effect=SpotifyException(404, -1, "Resource not found")
        )
        self.mocks["account"].async_get_internal_playlist_length = AsyncMock(
            return_value=None
        )

        self.resut = await async_random_index(
            self.mocks["account"],
            "spotify:playlist:37i9dQZF1DX4sWSpwq3LiO",
        )

    def test_returns_pseudo_random_offset(self):
        self.assertEqual(self.resut, 7)

    def test_offset_bounded_to_fallback_range(self):
        try:
            self.mocks["random"].assert_called_once_with(
                0, _RANDOM_FALLBACK_ITEMS - 1
            )
        except AssertionError as exc:
            self.fail(exc)


class TestPlaylistNotFoundInternalLength(IsolatedAsyncioTestCase):
    """When the public Web API 404s on an editorial playlist but the
    unofficial internal endpoint resolves its real length, the random
    start must span the whole playlist rather than the fallback window."""

    @patch(f"{TEST_MODULE}.randint", new_callable=MagicMock)
    async def asyncSetUp(self, mock_random: MagicMock):

        mock_random.return_value = 61

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount),
            "random": mock_random,
        }

        self.mocks["account"].async_get_playlist = AsyncMock(
            side_effect=SpotifyException(404, -1, "Resource not found")
        )
        self.mocks["account"].async_get_internal_playlist_length = AsyncMock(
            return_value=80
        )

        self.resut = await async_random_index(
            self.mocks["account"],
            "spotify:playlist:37i9dQZF1DX4sWSpwq3LiO",
        )

    def test_returns_internal_random_offset(self):
        self.assertEqual(self.resut, 61)

    def test_offset_spans_full_playlist(self):
        try:
            self.mocks["random"].assert_called_once_with(0, 79)
        except AssertionError as exc:
            self.fail(exc)


class TestPlaylistOtherSpotifyError(IsolatedAsyncioTestCase):
    """Non-404 Spotify errors must still propagate."""

    async def test_error_reraised(self):

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount)
        }

        self.mocks["account"].async_get_playlist = AsyncMock(
            side_effect=SpotifyException(500, -1, "Server Error")
        )

        with self.assertRaises(SpotifyException):
            await async_random_index(
                self.mocks["account"],
                "spotify:playlist:foo",
            )


class TestPlaylistWithItemsKeyRandInt(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.randint", new_callable=MagicMock)
    async def asyncSetUp(self, mock_random: MagicMock):

        mock_random.return_value = 7

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount)
        }

        self.mocks["account"].async_get_playlist = AsyncMock()
        self.mocks["account"].async_get_playlist.return_value = {
            "items": {
                "total": 53
            }
        }
        self.resut = await async_random_index(
            self.mocks["account"],
            "spotify:playlist:foo",
        )

    def test_received_expected_index(self):
        self.assertEqual(self.resut, 7)

    def test_randint_called_with_item_count(self):
        try:
            self.mocks["account"].async_get_playlist.assert_called()
        except AssertionError:
            self.fail()


class TestPlaylistWithoutTrackCountRandInt(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.randint", new_callable=MagicMock)
    async def asyncSetUp(self, mock_random: MagicMock):

        mock_random.return_value = 3
        self.mock_random = mock_random

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount)
        }

        self.mocks["account"].async_get_playlist = AsyncMock()
        self.mocks["account"].async_get_playlist.return_value = {
            "id": "foo"
        }
        self.mocks["account"].async_get_internal_playlist_length = AsyncMock(
            return_value=None
        )
        self.resut = await async_random_index(
            self.mocks["account"],
            "spotify:playlist:foo",
        )

    def test_received_expected_index(self):
        self.assertEqual(self.resut, 3)

    def test_falls_back_to_default_item_window(self):
        try:
            self.mock_random.assert_called_with(
                0,
                _RANDOM_FALLBACK_ITEMS - 1,
            )
        except AssertionError as exc:
            self.fail(exc)


class TestPlaylistNoCountInternalLength(IsolatedAsyncioTestCase):
    """When the Web API returns a playlist without a track count but the
    internal endpoint resolves the real length, span the whole playlist."""

    @patch(f"{TEST_MODULE}.randint", new_callable=MagicMock)
    async def asyncSetUp(self, mock_random: MagicMock):

        mock_random.return_value = 12
        self.mock_random = mock_random

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount)
        }

        self.mocks["account"].async_get_playlist = AsyncMock()
        self.mocks["account"].async_get_playlist.return_value = {
            "id": "foo"
        }
        self.mocks["account"].async_get_internal_playlist_length = AsyncMock(
            return_value=30
        )
        self.resut = await async_random_index(
            self.mocks["account"],
            "spotify:playlist:foo",
        )

    def test_received_expected_index(self):
        self.assertEqual(self.resut, 12)

    def test_offset_spans_full_playlist(self):
        try:
            self.mock_random.assert_called_with(0, 29)
        except AssertionError as exc:
            self.fail(exc)
