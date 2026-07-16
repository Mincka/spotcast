"""Module to test the apply_device_options and is_filtered methods"""

from unittest import TestCase
from unittest.mock import MagicMock

from custom_components.spotcast.media_player.device_manager import (
    DeviceManager,
    SpotifyAccount,
)


def build_manager() -> DeviceManager:
    account = MagicMock(spec=SpotifyAccount)
    account.name = "Dummy Account"
    return DeviceManager(account, MagicMock())


class TestDefaults(TestCase):

    def setUp(self):
        self.manager = build_manager()

    def test_default_timeout_is_class_constant(self):
        self.assertEqual(
            self.manager.stale_device_timeout,
            DeviceManager.STALE_DEVICE_TIMEOUT,
        )

    def test_nothing_filtered_by_default(self):
        self.assertFalse(self.manager.is_filtered("Living Room Jam"))


class TestApplyOptions(TestCase):

    def setUp(self):
        self.manager = build_manager()
        self.manager.apply_device_options({
            "stale_device_timeout": 2,
            "device_filter_mode": "deny",
            "device_filter_patterns": "*Jam*, Guest Phone",
        })

    def test_timeout_converted_to_seconds(self):
        self.assertEqual(self.manager.stale_device_timeout, 2 * 24 * 3600)

    def test_patterns_parsed(self):
        self.assertEqual(
            self.manager.filter_patterns,
            ["*Jam*", "Guest Phone"],
        )


class TestDenyMode(TestCase):

    def setUp(self):
        self.manager = build_manager()
        self.manager.apply_device_options({
            "stale_device_timeout": 7,
            "device_filter_mode": "deny",
            "device_filter_patterns": "*jam*",
        })

    def test_matching_device_filtered(self):
        self.assertTrue(self.manager.is_filtered("Living Room JAM"))

    def test_non_matching_device_kept(self):
        self.assertFalse(self.manager.is_filtered("Kitchen Speaker"))


class TestAllowMode(TestCase):

    def setUp(self):
        self.manager = build_manager()
        self.manager.apply_device_options({
            "stale_device_timeout": 7,
            "device_filter_mode": "allow",
            "device_filter_patterns": "Kitchen*, JULIEN-PC",
        })

    def test_listed_device_kept(self):
        self.assertFalse(self.manager.is_filtered("Kitchen Speaker"))

    def test_unlisted_device_filtered(self):
        self.assertTrue(self.manager.is_filtered("Living Room Jam"))


class TestAllowModeWithoutPatterns(TestCase):
    """Allow mode with no patterns would remove every device. The
    filter must be ignored instead."""

    def setUp(self):
        self.manager = build_manager()
        self.manager.apply_device_options({
            "stale_device_timeout": 7,
            "device_filter_mode": "allow",
            "device_filter_patterns": " ",
        })

    def test_nothing_filtered(self):
        self.assertFalse(self.manager.is_filtered("Kitchen Speaker"))


class TestFilteredDeviceSkipped(TestCase):

    def setUp(self):
        self.manager = build_manager()
        self.manager._account.id = "dummy"
        self.manager.apply_device_options({
            "stale_device_timeout": 7,
            "device_filter_mode": "deny",
            "device_filter_patterns": "*Jam*",
        })

        self.result = self.manager._key_current_devices([
            {"id": "abc123", "name": "Kitchen Speaker", "type": "Speaker"},
            {"id": "def456", "name": "Family Jam", "type": "Smartphone"},
        ])

    def test_only_unfiltered_device_kept(self):
        names = [device["name"] for device in self.result.values()]
        self.assertEqual(names, ["Kitchen Speaker"])
