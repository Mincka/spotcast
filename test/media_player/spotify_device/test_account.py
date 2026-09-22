"""Module to test the account property of the SpotifyDevice class"""

from unittest import TestCase
from unittest.mock import MagicMock

from custom_components.spotcast.media_player.spotify_player import (
    SpotifyAccount,
    SpotifyDevice,
)


class TestValue(TestCase):

    def setUp(self):

        self.mock_account = MagicMock(spec=SpotifyAccount)
        self.mock_account.id = "dummy"
        self.mock_account.name = "Dummy User"

        self.device = SpotifyDevice(
            self.mock_account,
            {
                "id": "12345",
                "name": "dummy_device",
                "type": "dummy",
            }
        )

    def test_account_is_the_owner(self):
        self.assertIs(self.device.account, self.mock_account)
