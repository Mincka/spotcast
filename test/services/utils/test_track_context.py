"""Module to test the track_context validator and EXTRAS_SCHEMA"""

from unittest import TestCase

import voluptuous as vol

from custom_components.spotcast.services.utils import (
    track_context,
    EXTRAS_SCHEMA,
)


class TestAcceptedValues(TestCase):

    def test_keyword_track(self):
        self.assertEqual(track_context("track"), "track")

    def test_keyword_album(self):
        self.assertEqual(track_context("album"), "album")

    def test_album_uri(self):
        uri = "spotify:album:1chw1DFmefTueG1VbNVoGN"
        self.assertEqual(track_context(uri), uri)

    def test_playlist_uri(self):
        uri = "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"
        self.assertEqual(track_context(uri), uri)


class TestRejectedValues(TestCase):

    def test_unknown_keyword_rejected(self):
        with self.assertRaises(vol.Invalid):
            track_context("artist")

    def test_unsupported_uri_type_rejected(self):
        with self.assertRaises(vol.Invalid):
            track_context("spotify:artist:0OdUWJ0sBjDrqHygGUXeCF")

    def test_garbage_rejected(self):
        with self.assertRaises(vol.Invalid):
            track_context("not a context")


class TestThroughExtrasSchema(TestCase):

    def test_playlist_uri_passes_extras_schema(self):
        uri = "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"
        result = EXTRAS_SCHEMA({"track_context": uri})
        self.assertEqual(result["track_context"], uri)

    def test_invalid_track_context_fails_extras_schema(self):
        with self.assertRaises(vol.Invalid):
            EXTRAS_SCHEMA({"track_context": "spotify:artist:foo"})
