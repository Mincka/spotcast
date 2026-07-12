"""Module to test the _update_from_coordinator function"""

from unittest import TestCase
from unittest.mock import MagicMock

from homeassistant.const import STATE_OFF

from custom_components.spotcast.coordinator import SpotcastCoordinator
from custom_components.spotcast.spotify import SpotifyAccount
from custom_components.spotcast.sensor.spotify_current_context_sensor import (
    SpotifyCurrentContextSensor,
)


def _build_sensor(data: dict) -> SpotifyCurrentContextSensor:
    coordinator = MagicMock(spec=SpotcastCoordinator)
    coordinator.account = MagicMock(spec=SpotifyAccount)
    coordinator.account.name = "Dummy Account"
    coordinator.account.id = "dummy_account"
    coordinator.data = data

    sensor = SpotifyCurrentContextSensor(coordinator)
    sensor._update_from_coordinator()
    return sensor


class TestPlaylistPlaying(TestCase):

    def setUp(self):
        self.sensor = _build_sensor(
            {
                "context_name": "Today's Top Hits",
                "playback_state": {
                    "context": {
                        "uri": "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",
                        "type": "playlist",
                    }
                },
            }
        )

    def test_state_is_playlist_name(self):
        self.assertEqual(self.sensor.state, "Today's Top Hits")

    def test_attributes_expose_context(self):
        self.assertEqual(
            self.sensor.extra_state_attributes,
            {
                "context_uri": "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",
                "context_type": "playlist",
            },
        )


class TestNothingResolved(TestCase):

    def setUp(self):
        self.sensor = _build_sensor(
            {
                "context_name": None,
                "playback_state": {},
            }
        )

    def test_state_is_inactive(self):
        self.assertEqual(self.sensor.state, STATE_OFF)

    def test_attributes_cleared(self):
        self.assertIsNone(self.sensor.extra_state_attributes)


class TestMissingPlaybackContext(TestCase):
    """A resolved name with a playback_state that has no context still
    reports the name and tolerates the missing context gracefully."""

    def setUp(self):
        self.sensor = _build_sensor(
            {
                "context_name": "RapCaviar",
                "playback_state": {},
            }
        )

    def test_state_is_playlist_name(self):
        self.assertEqual(self.sensor.state, "RapCaviar")

    def test_attributes_have_none_context(self):
        self.assertEqual(
            self.sensor.extra_state_attributes,
            {"context_uri": None, "context_type": None},
        )
