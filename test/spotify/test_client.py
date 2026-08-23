"""Module to test the extended spotipy client"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from spotipy import Spotify as SpotipyClient

from custom_components.spotcast.spotify.client import (
    Spotify,
    SpotifyException,
    RateLimitedError,
)
from custom_components.spotcast.spotify.rate_limit import (
    RateLimitGuard,
    DEFAULT_RETRY_AFTER,
)

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


def rate_limited(retry_after: str | None = "120") -> SpotifyException:
    """Builds the exception spotipy raises on a 429."""
    headers = {"Retry-After": retry_after} if retry_after else {}
    return SpotifyException(
        429,
        -1,
        "url:\n API rate limit exceeded",
        headers=headers,
    )


class TestRateLimitRetriesDisabled(TestCase):
    """spotipy must not sleep on a 429 inside the executor thread."""

    def test_429_not_in_retry_codes(self):
        client = Spotify(auth="dummy")
        self.assertNotIn(429, client.status_forcelist)

    def test_server_errors_still_retried(self):
        client = Spotify(auth="dummy")
        for code in (500, 502, 503, 504):
            self.assertIn(code, client.status_forcelist)

    def test_explicit_forcelist_respected(self):
        client = Spotify(auth="dummy", status_forcelist=(503,))
        self.assertEqual(client.status_forcelist, (503,))


class TestRateLimitResponse(TestCase):

    @patch.object(SpotipyClient, "_internal_call")
    def setUp(self, mock_call: MagicMock):
        self.mock_call = mock_call
        self.mock_call.side_effect = rate_limited("120")

        self.guard = RateLimitGuard()
        self.client = Spotify(auth="dummy", rate_limit_guard=self.guard)

        with self.assertRaises(RateLimitedError) as ctx:
            self.client._internal_call(*CALL_ARGS)

        self.error = ctx.exception

    def test_window_registered_from_header(self):
        self.assertTrue(self.guard.is_limited)
        self.assertAlmostEqual(self.guard.seconds_remaining, 120, delta=2)

    def test_error_carries_retry_at(self):
        self.assertEqual(self.error.retry_at, self.guard.retry_at)

    def test_error_is_a_spotify_exception(self):
        self.assertIsInstance(self.error, SpotifyException)
        self.assertEqual(self.error.http_status, 429)

    def test_call_not_retried(self):
        self.assertEqual(self.mock_call.call_count, 1)


class TestRateLimitResponseWithoutHeader(TestCase):

    @patch.object(SpotipyClient, "_internal_call")
    def test_default_window_registered(self, mock_call: MagicMock):
        mock_call.side_effect = rate_limited(None)
        guard = RateLimitGuard()
        client = Spotify(auth="dummy", rate_limit_guard=guard)

        with self.assertRaises(RateLimitedError):
            client._internal_call(*CALL_ARGS)

        self.assertTrue(guard.is_limited)
        self.assertAlmostEqual(
            guard.seconds_remaining,
            DEFAULT_RETRY_AFTER,
            delta=2,
        )


class TestCallSkippedWhileLimited(TestCase):
    """Every client sharing the guard fails fast, without a network
    call, until the window expires."""

    @patch.object(SpotipyClient, "_internal_call")
    def setUp(self, mock_call: MagicMock):
        self.mock_call = mock_call
        self.guard = RateLimitGuard()
        self.guard.register("120")

        self.other_client = Spotify(auth="other", rate_limit_guard=self.guard)

        with self.assertRaises(RateLimitedError):
            self.other_client._internal_call(*CALL_ARGS)

    def test_no_network_call_made(self):
        self.mock_call.assert_not_called()


class TestCallResumesAfterWindow(TestCase):

    @patch.object(SpotipyClient, "_internal_call")
    def test_call_goes_through(self, mock_call: MagicMock):
        mock_call.return_value = {"devices": []}
        guard = RateLimitGuard()
        guard.register("0")

        client = Spotify(auth="dummy", rate_limit_guard=guard)
        result = client._internal_call(*CALL_ARGS)

        self.assertEqual(result, {"devices": []})
        mock_call.assert_called_once()


class TestFakeRateLimitOnServerErrors(TestCase):
    """spotipy reports exhausted 5xx retries as a 429. Those are not a
    rate limit and must not pause the other accounts."""

    @patch.object(SpotipyClient, "_internal_call")
    def test_guard_not_triggered(self, mock_call: MagicMock):
        mock_call.side_effect = SpotifyException(
            429,
            -1,
            "url:\n Max Retries",
            reason="too many 502 error responses",
        )
        guard = RateLimitGuard()
        client = Spotify(auth="dummy", rate_limit_guard=guard)

        with self.assertRaises(SpotifyException) as ctx:
            client._internal_call(*CALL_ARGS)

        self.assertNotIsInstance(ctx.exception, RateLimitedError)
        self.assertFalse(guard.is_limited)


class TestRateLimitOnUnauthorizedRetry(TestCase):

    @patch.object(SpotipyClient, "_internal_call")
    def test_429_on_retry_registered(self, mock_call: MagicMock):
        mock_call.side_effect = [unauthorized(), rate_limited("90")]
        guard = RateLimitGuard()
        client = Spotify(
            auth="stale",
            token_refresher=MagicMock(return_value="fresh"),
            rate_limit_guard=guard,
        )

        with self.assertRaises(RateLimitedError):
            client._internal_call(*CALL_ARGS)

        self.assertTrue(guard.is_limited)
        self.assertEqual(mock_call.call_count, 2)
