"""Module to test the extended spotipy client"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from custom_components.spotcast.spotify.client import Spotify


class TestSaveToLibrary(TestCase):

    @patch.object(Spotify, "_put")
    def setUp(self, mock_put: MagicMock):
        self.mock_put = mock_put
        self.client = Spotify(auth="dummy")
        self.client.save_to_library([
            "spotify:track:foo",
            "spotify:track:bar",
        ])

    def test_put_called_with_library_endpoint(self):
        try:
            self.mock_put.assert_called_with(
                "me/library?uris=spotify:track:foo,spotify:track:bar"
            )
        except AssertionError:
            self.fail()


class TestRemoveFromLibrary(TestCase):

    @patch.object(Spotify, "_delete")
    def setUp(self, mock_delete: MagicMock):
        self.mock_delete = mock_delete
        self.client = Spotify(auth="dummy")
        self.client.remove_from_library(["spotify:track:foo"])

    def test_delete_called_with_library_endpoint(self):
        try:
            self.mock_delete.assert_called_with(
                "me/library?uris=spotify:track:foo"
            )
        except AssertionError:
            self.fail()


class TestPlaylistItems(TestCase):

    @patch.object(Spotify, "_get")
    def setUp(self, mock_get: MagicMock):
        self.mock_get = mock_get
        self.client = Spotify(auth="dummy")
        self.client.playlist_items(
            "spotify:playlist:foo",
            None,
            50,
            10,
            "CA",
        )

    def test_get_called_with_items_endpoint(self):
        try:
            self.mock_get.assert_called_with(
                "playlists/foo/items",
                fields=None,
                limit=50,
                offset=10,
                market="CA",
            )
        except AssertionError:
            self.fail()
