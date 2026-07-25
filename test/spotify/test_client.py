"""Module to test the extended spotipy client"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from spotipy import Spotify as SpotipyClient

from custom_components.spotcast.spotify.client import Spotify, SpotifyException

CALL_ARGS = ("GET", "me/player/devices", None, {})


def unauthorized() -> SpotifyException:
    """Builds the exception spotipy raises on a 401."""
    return SpotifyException(401, -1, "url:\n Access token missing")


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


class TestUnauthorizedRetry(TestCase):

    @patch.object(SpotipyClient, "_internal_call")
    def setUp(self, mock_call: MagicMock):
        self.mock_call = mock_call
        self.mock_call.side_effect = [unauthorized(), {"devices": []}]

        self.refresher = MagicMock(return_value="fresh")
        self.client = Spotify(auth="stale", token_refresher=self.refresher)

        self.result = self.client._internal_call(*CALL_ARGS)

    def test_result_of_the_retry_returned(self):
        self.assertEqual(self.result, {"devices": []})

    def test_token_refresh_forced(self):
        self.refresher.assert_called_once_with()

    def test_fresh_token_applied_to_the_client(self):
        self.assertEqual(self.client._auth, "fresh")

    def test_call_retried_once(self):
        self.assertEqual(self.mock_call.call_count, 2)


class TestUnauthorizedWithoutRefresher(TestCase):

    @patch.object(SpotipyClient, "_internal_call")
    def test_exception_raised(self, mock_call: MagicMock):
        mock_call.side_effect = unauthorized()
        client = Spotify(auth="stale")

        with self.assertRaises(SpotifyException):
            client._internal_call(*CALL_ARGS)

        self.assertEqual(mock_call.call_count, 1)


class TestUnauthorizedWithFailingRefresh(TestCase):

    @patch.object(SpotipyClient, "_internal_call")
    def test_original_error_raised(self, mock_call: MagicMock):
        mock_call.side_effect = unauthorized()
        refresher = MagicMock(side_effect=ConnectionError("no token"))
        client = Spotify(auth="stale", token_refresher=refresher)

        with self.assertRaises(SpotifyException) as ctx:
            client._internal_call(*CALL_ARGS)

        self.assertEqual(ctx.exception.http_status, 401)
        self.assertEqual(mock_call.call_count, 1)


class TestOtherErrorNotRetried(TestCase):

    @patch.object(SpotipyClient, "_internal_call")
    def test_exception_raised_without_retry(self, mock_call: MagicMock):
        mock_call.side_effect = SpotifyException(404, -1, "url:\n Not found")
        refresher = MagicMock(return_value="fresh")
        client = Spotify(auth="valid", token_refresher=refresher)

        with self.assertRaises(SpotifyException):
            client._internal_call(*CALL_ARGS)

        self.assertEqual(mock_call.call_count, 1)
        refresher.assert_not_called()
