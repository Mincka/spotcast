"""Module to test the _update_from_coordinator function"""

from unittest import TestCase
from unittest.mock import MagicMock

from custom_components.spotcast.coordinator import SpotcastCoordinator
from custom_components.spotcast.spotify import SpotifyAccount
from custom_components.spotcast.sensor.spotify_liked_songs_sensor import (
    SpotifyLikedSongsSensor,
)


class TestSuccessfulUpdate(TestCase):

    def setUp(self):

        self.coordinator = MagicMock(spec=SpotcastCoordinator)
        self.coordinator.account = MagicMock(spec=SpotifyAccount)
        self.coordinator.account.name = "Dummy Account"
        self.coordinator.data = {"liked_songs_count": 2}

        self.sensor = SpotifyLikedSongsSensor(self.coordinator)
        self.sensor._update_from_coordinator()

    def test_attribute_state_was_set_to_liked_songs_count(self):
        self.assertEqual(self.sensor.state, 2)
