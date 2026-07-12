"""Module to test the _update_from_coordinator function"""

from unittest import TestCase
from unittest.mock import MagicMock

from custom_components.spotcast.coordinator import SpotcastCoordinator
from custom_components.spotcast.spotify import SpotifyAccount
from custom_components.spotcast.sensor.spotify_profile_sensor import (
    SpotifyProfileSensor,
    STATE_OK,
)


class TestSuccessfulUpdate(TestCase):

    def setUp(self):

        self.coordinator = MagicMock(spec=SpotcastCoordinator)
        self.coordinator.account = MagicMock(spec=SpotifyAccount)
        self.coordinator.account.name = "Dummy Account"
        self.coordinator.account.entry_id = "12345"
        self.coordinator.data = {
            "profile": {
                "id": "dummy_id",
                "explicit_content": {
                    "filter_enabled": False,
                    "filter_locked": False,
                },
                "followers": {
                    "total": 10
                },
                "href": "http://locahost",
                "external_urls": {
                    "spotify": "http://locahost"
                },
                "images": [
                    {
                        "url": "http://locahost",
                        "height": 640,
                        "width": 640,
                    }
                ]
            }
        }

        self.sensor = SpotifyProfileSensor(self.coordinator)
        self.sensor._update_from_coordinator()

    def test_attribute_state_was_set_to_ok(self):
        self.assertEqual(self.sensor.state, STATE_OK)

    def test_extra_attributes_saved(self):
        self.assertEqual(
            self.sensor.extra_state_attributes,
            {
                "id": "dummy_id",
                "filter_explicit_enabled": False,
                "filter_explicit_locked": False,
                "followers_count": 10,
                "entry_id": "12345",
            },
        )

    def test_raw_profile_not_modified(self):
        self.assertIn("followers", self.coordinator.data["profile"])
