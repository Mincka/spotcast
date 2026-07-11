"""Module to test the suppress_playlist_404_logs context manager"""

import logging
from unittest import TestCase

from custom_components.spotcast.spotify.utils import suppress_playlist_404_logs

PLAYLIST_404 = (
    "HTTP Error for GET to "
    "https://api.spotify.com/v1/playlists/37i9dQZF1DX1tuUiirhaT3 "
    "with Params: {} returned 404 due to Resource not found"
)


class _CollectingHandler(logging.Handler):
    """Captures emitted records so the test can assert on them."""

    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


class TestSuppressPlaylist404Logs(TestCase):

    def setUp(self):
        self.logger = logging.getLogger("spotipy.client")
        self.handler = _CollectingHandler()
        self.logger.addHandler(self.handler)
        self._previous_level = self.logger.level
        self.logger.setLevel(logging.DEBUG)

    def tearDown(self):
        self.logger.removeHandler(self.handler)
        self.logger.setLevel(self._previous_level)

    def test_playlist_404_is_dropped(self):
        with suppress_playlist_404_logs():
            self.logger.error(PLAYLIST_404)

        self.assertEqual(self.handler.records, [])

    def test_non_404_error_passes(self):
        with suppress_playlist_404_logs():
            self.logger.error(
                "HTTP Error for GET to "
                "https://api.spotify.com/v1/playlists/foo "
                "with Params: {} returned 500 due to Server Error"
            )

        self.assertEqual(len(self.handler.records), 1)

    def test_non_playlist_404_passes(self):
        with suppress_playlist_404_logs():
            self.logger.error(
                "HTTP Error for GET to "
                "https://api.spotify.com/v1/albums/foo "
                "with Params: {} returned 404 due to Resource not found"
            )

        self.assertEqual(len(self.handler.records), 1)

    def test_filter_removed_after_context(self):
        with suppress_playlist_404_logs():
            pass

        self.logger.error(PLAYLIST_404)

        self.assertEqual(len(self.handler.records), 1)
