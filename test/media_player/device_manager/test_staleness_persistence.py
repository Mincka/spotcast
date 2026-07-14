"""Module to test the persisted staleness tracking and the purge of
entities restored from previous runs"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from custom_components.spotcast.media_player.device_manager import (
    DeviceManager,
    SpotifyAccount,
)

TEST_MODULE = "custom_components.spotcast.media_player.device_manager"


def build_manager() -> DeviceManager:
    account = MagicMock(spec=SpotifyAccount)
    account.name = "Dummy Account"
    account.entry_id = "12345"
    account.hass = MagicMock()
    manager = DeviceManager(account, MagicMock())
    manager._staleness_store = MagicMock()
    manager._staleness_store.async_load = AsyncMock(return_value=None)
    manager._staleness_store.async_save = AsyncMock()
    return manager


def registry_entry(unique_id: str, entity_id: str, domain="media_player"):
    entry = MagicMock()
    entry.domain = domain
    entry.unique_id = unique_id
    entry.entity_id = entity_id
    return entry


class TestLoadStaleTimestamps(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.manager = build_manager()
        self.manager._staleness_store.async_load = AsyncMock(
            return_value={"foo": 1_000.0, "bar": 2_000.0}
        )
        self.manager.unavailable_since["bar"] = 3_000.0

        await self.manager._async_load_stale_timestamps()

    def test_stored_timestamp_loaded(self):
        self.assertEqual(self.manager.unavailable_since["foo"], 1_000.0)

    def test_in_memory_timestamp_wins(self):
        self.assertEqual(self.manager.unavailable_since["bar"], 3_000.0)

    async def test_second_load_skipped(self):
        await self.manager._async_load_stale_timestamps()
        self.manager._staleness_store.async_load.assert_awaited_once()


class TestSaveStaleTimestamps(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.manager = build_manager()
        self.manager.unavailable_since["foo"] = 1_000.0

    async def test_no_save_before_load(self):
        await self.manager._async_save_stale_timestamps()
        self.manager._staleness_store.async_save.assert_not_called()

    async def test_saved_after_load(self):
        await self.manager._async_load_stale_timestamps()
        await self.manager._async_save_stale_timestamps()
        self.manager._staleness_store.async_save.assert_awaited_with(
            {"foo": 1_000.0}
        )

    async def test_unchanged_data_not_saved_twice(self):
        await self.manager._async_load_stale_timestamps()
        await self.manager._async_save_stale_timestamps()
        await self.manager._async_save_stale_timestamps()
        self.manager._staleness_store.async_save.assert_awaited_once()


class TestOrphanSweep(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_entries_for_config_entry")
    @patch(f"{TEST_MODULE}.async_get_er")
    async def asyncSetUp(
        self,
        mock_er: MagicMock,
        mock_entries: MagicMock,
    ):
        self.manager = build_manager()
        self.manager.tracked_devices["tracked_key"] = MagicMock()

        mock_entries.return_value = [
            registry_entry(
                "orphan_key_spotcast_device",
                "media_player.orphan",
            ),
            registry_entry(
                "tracked_key_spotcast_device",
                "media_player.tracked",
            ),
            registry_entry(
                "unrelated",
                "sensor.profile",
                domain="sensor",
            ),
        ]

        self.manager._sweep_orphaned_entities()

    def test_orphan_registered(self):
        self.assertEqual(
            self.manager.orphaned_entities,
            {"orphan_key": "media_player.orphan"},
        )

    def test_orphan_aging_started(self):
        self.assertIn("orphan_key", self.manager.unavailable_since)


class TestOrphanPurge(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_get_er")
    async def asyncSetUp(self, mock_er: MagicMock):
        self.manager = build_manager()
        self.mock_registry = MagicMock()
        mock_er.return_value = self.mock_registry

        self.manager.remove_device = MagicMock()
        self.manager.orphaned_entities["orphan_key"] = "media_player.orphan"
        self.manager.unavailable_since["orphan_key"] = 1_000.0

        await self.manager._async_purge_orphaned_entities(
            1_000.0 + self.manager.stale_device_timeout + 1
        )

    def test_entity_removed_from_registry(self):
        try:
            self.mock_registry.async_remove.assert_called_with(
                "media_player.orphan"
            )
        except AssertionError:
            self.fail()

    def test_device_removed(self):
        try:
            self.manager.remove_device.assert_called_with(
                {("spotcast", "orphan_key")}
            )
        except AssertionError:
            self.fail()

    def test_orphan_no_longer_tracked(self):
        self.assertEqual(self.manager.orphaned_entities, {})
        self.assertNotIn("orphan_key", self.manager.unavailable_since)


class TestFreshOrphanKept(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_get_er")
    async def asyncSetUp(self, mock_er: MagicMock):
        self.manager = build_manager()
        self.mock_registry = MagicMock()
        mock_er.return_value = self.mock_registry

        self.manager.orphaned_entities["orphan_key"] = "media_player.orphan"
        self.manager.unavailable_since["orphan_key"] = 1_000.0

        await self.manager._async_purge_orphaned_entities(1_001.0)

    def test_entity_kept(self):
        try:
            self.mock_registry.async_remove.assert_not_called()
        except AssertionError:
            self.fail()

    def test_orphan_still_tracked(self):
        self.assertIn("orphan_key", self.manager.orphaned_entities)
