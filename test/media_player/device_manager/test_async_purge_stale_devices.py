"""Module to test the async_purge_stale_devices method"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from custom_components.spotcast.media_player.device_manager import (
    DeviceManager,
    SpotifyDevice,
    SpotifyAccount,
)

TEST_MODULE = "custom_components.spotcast.media_player.device_manager"


def build_manager() -> tuple[DeviceManager, MagicMock]:
    account = MagicMock(spec=SpotifyAccount)
    account.name = "Dummy Account"
    manager = DeviceManager(account, MagicMock())
    device = MagicMock(spec=SpotifyDevice)
    device.name = "Old Jam Device"
    device.device_info = {"identifiers": {("spotcast", "foo")}}
    device.async_remove = AsyncMock()
    manager.unavailable_devices["foo"] = device
    manager.remove_device = MagicMock()
    return manager, device


class TestStaleDevicePurged(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.time", new_callable=MagicMock)
    async def asyncSetUp(self, mock_time: MagicMock):
        self.manager, self.device = build_manager()
        self.manager.unavailable_since["foo"] = 1_000
        mock_time.return_value = (
            1_000 + DeviceManager.STALE_DEVICE_TIMEOUT + 1
        )
        await self.manager.async_purge_stale_devices()

    def test_entity_removed(self):
        try:
            self.device.async_remove.assert_awaited_with(force_remove=True)
        except AssertionError as exc:
            self.fail(exc)

    def test_registry_entry_removed(self):
        try:
            self.manager.remove_device.assert_called_with(
                {("spotcast", "foo")}
            )
        except AssertionError as exc:
            self.fail(exc)

    def test_device_no_longer_tracked(self):
        self.assertNotIn("foo", self.manager.unavailable_devices)
        self.assertNotIn("foo", self.manager.unavailable_since)


class TestFreshDeviceKept(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.time", new_callable=MagicMock)
    async def asyncSetUp(self, mock_time: MagicMock):
        self.manager, self.device = build_manager()
        self.manager.unavailable_since["foo"] = 1_000
        mock_time.return_value = 1_000 + 60
        await self.manager.async_purge_stale_devices()

    def test_entity_not_removed(self):
        try:
            self.device.async_remove.assert_not_called()
        except AssertionError as exc:
            self.fail(exc)

    def test_device_still_tracked(self):
        self.assertIn("foo", self.manager.unavailable_devices)


class TestMissingRegistryEntryTolerated(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.time", new_callable=MagicMock)
    async def asyncSetUp(self, mock_time: MagicMock):
        self.manager, self.device = build_manager()
        self.manager.unavailable_since["foo"] = 1_000
        self.manager.remove_device.side_effect = KeyError("gone")
        mock_time.return_value = (
            1_000 + DeviceManager.STALE_DEVICE_TIMEOUT + 1
        )
        await self.manager.async_purge_stale_devices()

    def test_device_no_longer_tracked(self):
        self.assertNotIn("foo", self.manager.unavailable_devices)
