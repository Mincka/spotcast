"""Module to test the is_group property of the chromecast_player. It is
True only when the underlying cast device is a speaker group."""

from unittest import TestCase
from unittest.mock import patch, MagicMock

from pychromecast import CastInfo

from homeassistant.components.cast.helpers import ChromeCastZeroconf

from custom_components.spotcast.media_player.chromecast_player import (
    Chromecast,
)


class TestGroupDevice(TestCase):

    @patch.object(Chromecast, "name")
    def setUp(self, mock_name: MagicMock):
        mock_name.return_value = "foo"
        mock_cast_info = MagicMock(spec=CastInfo)
        mock_cast_info.cast_type = "group"
        mock_cast_info.friendly_name = "All Speakers"
        mock_cast_info.services = ["hello", "world"]
        self.device = Chromecast(
            mock_cast_info,
            zconf=MagicMock(spec=ChromeCastZeroconf),
        )

    def test_is_group_true(self):
        self.assertTrue(self.device.is_group)


class TestSingleDevice(TestCase):

    @patch.object(Chromecast, "name")
    def setUp(self, mock_name: MagicMock):
        mock_name.return_value = "foo"
        mock_cast_info = MagicMock(spec=CastInfo)
        mock_cast_info.cast_type = "cast"
        mock_cast_info.friendly_name = "Living Room"
        mock_cast_info.services = ["hello", "world"]
        self.device = Chromecast(
            mock_cast_info,
            zconf=MagicMock(spec=ChromeCastZeroconf),
        )

    def test_is_group_false(self):
        self.assertFalse(self.device.is_group)
