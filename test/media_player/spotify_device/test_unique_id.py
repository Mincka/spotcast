"""Module to test the unique_id property"""

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

        self.device = SpotifyDevice(
            self.mock_account,
            {
                "id": "12345",
                "name": "dummy_device",
                "type": "dummy",
            }
        )

    def test_unique_id_value(self):
        self.assertEqual(
            self.device.unique_id,
            "dummy_device_dummy_spotcast_device",
        )


class TestStableAcrossDeviceIdChange(TestCase):
    """The unique id must be based on the device name, not the Spotify
    device id, so it stays stable when Spotify assigns the device a new
    id between sessions (see #580, #586)."""

    def setUp(self):

        self.mock_account = MagicMock(spec=SpotifyAccount)
        self.mock_account.id = "dummy"

        self.device = SpotifyDevice(
            self.mock_account,
            {
                "id": "12345",
                "name": "dummy_device",
                "type": "dummy",
            }
        )

    def test_unique_id_unchanged_when_device_id_changes(self):
        before = self.device.unique_id
        self.device.device_data = {
            "id": "a-brand-new-id",
            "name": "dummy_device",
            "type": "dummy",
        }
        self.assertEqual(self.device.unique_id, before)


class TestExplicitIdentityKey(TestCase):
    """The DeviceManager can pass an explicit identity key to
    disambiguate devices that share a name."""

    def setUp(self):

        self.mock_account = MagicMock(spec=SpotifyAccount)
        self.mock_account.id = "dummy"

        self.device = SpotifyDevice(
            self.mock_account,
            {
                "id": "12345",
                "name": "dummy_device",
                "type": "dummy",
            },
            identity_key="dummy_device_dummy_12345",
        )

    def test_unique_id_uses_explicit_key(self):
        self.assertEqual(
            self.device.unique_id,
            "dummy_device_dummy_12345_spotcast_device",
        )

    def test_entity_id_uses_explicit_key(self):
        self.assertEqual(
            self.device.entity_id,
            "media_player.dummy_device_dummy_12345_spotcast",
        )
