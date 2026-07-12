"""Module to test the async_update function"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from custom_components.spotcast.media_player.device_manager import (
    DeviceManager,
    SpotifyAccount,
    SpotifyDevice,
    AddEntitiesCallback,
    RetrySupervisor,
)

from test.media_player.device_manager import TEST_MODULE

# identity key for a device named "dummy device" on account "dummy"
KEY = "dummy_device_dummy"
WEB_KEY = "web_player_dummy_dummy"


def _registry_without_legacy():
    """A registry mock where no legacy entity exists, so the lazy
    migration is a no-op."""
    registry = MagicMock()
    registry.async_get_entity_id = MagicMock(return_value=None)
    return registry


class TestSupervisorNotReady(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount),
            "callback": MagicMock(spec=AddEntitiesCallback),
            "supervisor": MagicMock(spec=RetrySupervisor)
        }

        self.mocks["account"].async_devices = AsyncMock()

        self.device_manager = DeviceManager(
            account=self.mocks["account"],
            async_add_entitites=self.mocks["callback"]
        )

        self.device_manager.supervisor = self.mocks["supervisor"]
        self.device_manager.supervisor.is_ready = False
        await self.device_manager.async_update()

    def test_account_devices_not_called(self):
        try:
            self.mocks["account"].async_devices.assert_not_called()
        except AssertionError:
            self.fail()


class TestFailedToRetrieveDevices(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount),
            "callback": MagicMock(spec=AddEntitiesCallback),
            "supervisor": MagicMock(spec=RetrySupervisor)
        }

        self.mocks["account"].async_devices = AsyncMock()
        self.mocks["account"].async_devices.side_effect = RetrySupervisor\
            .SUPERVISED_EXCEPTIONS[0]()

        self.mocks["supervisor"].log_message = MagicMock()

        self.device_manager = DeviceManager(
            account=self.mocks["account"],
            async_add_entitites=self.mocks["callback"]
        )

        self.device_manager.supervisor = self.mocks["supervisor"]
        self.device_manager.supervisor.is_ready = True
        self.device_manager.supervisor.SUPERVISED_EXCEPTIONS = RetrySupervisor\
            .SUPERVISED_EXCEPTIONS
        await self.device_manager.async_update()

    def test_supervisor_set_to_unhealthy(self):
        self.assertFalse(self.mocks["supervisor"]._is_healthy)

    def test_error_was_logged(self):
        try:
            self.mocks["supervisor"].log_message.assert_called()
        except AssertionError:
            self.fail()


class TestNewDevices(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_get_er")
    async def asyncSetUp(self, mock_er: MagicMock):

        mock_er.return_value = _registry_without_legacy()

        self.mock_account = MagicMock(spec=SpotifyAccount)
        self.mock_account.id = "dummy"
        self.mock_account.hass = MagicMock()
        self.mock_callack = MagicMock(spec=AddEntitiesCallback)

        self.mock_account.async_devices = AsyncMock(
            return_value=[
                {
                    "id": "1234",
                    "name": "dummy device",
                    "type": "Computer",
                }
            ]
        )
        self.mock_account.async_playback_state = AsyncMock(return_value={})

        self.device_manager = DeviceManager(
            self.mock_account,
            self.mock_callack,
        )

        await self.device_manager.async_update()

    async def test_device_added_to_tracked(self):
        self.assertEqual(len(self.device_manager.tracked_devices), 1)
        self.assertIn(KEY, self.device_manager.tracked_devices)

    async def test_entity_was_added(self):
        try:
            self.mock_callack.assert_called()
        except AssertionError:
            self.fail()


class TestNewWebPlayer(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_get_er")
    async def asyncSetUp(self, mock_er: MagicMock):

        mock_er.return_value = _registry_without_legacy()

        self.mock_account = MagicMock(spec=SpotifyAccount)
        self.mock_account.id = "dummy"
        self.mock_account.hass = MagicMock()
        self.mock_callack = MagicMock(spec=AddEntitiesCallback)

        self.mock_account.async_devices = AsyncMock(
            return_value=[
                {
                    "id": "1234",
                    "name": "Web Player (Dummy)",
                    "type": "Computer",
                }
            ]
        )
        self.mock_account.async_playback_state = AsyncMock(return_value={})

        self.device_manager = DeviceManager(
            self.mock_account,
            self.mock_callack,
        )

        await self.device_manager.async_update()

    def test_device_added_to_tracked(self):
        self.assertEqual(len(self.device_manager.tracked_devices), 1)
        self.assertIn(WEB_KEY, self.device_manager.tracked_devices)

    def test_device_class_changed_to_web_player(self):
        self.assertEqual(
            self.device_manager.tracked_devices[WEB_KEY].device_data["type"],
            "Web Player",
        )

    def test_entity_was_added(self):
        try:
            self.mock_callack.assert_called()
        except AssertionError:
            self.fail()


class TestIgnoredDevice(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self.mock_account = MagicMock(spec=SpotifyAccount)
        self.mock_account.id = "dummy"
        self.mock_account.hass = MagicMock()
        self.mock_callack = MagicMock(spec=AddEntitiesCallback)

        self.mock_account.async_devices = AsyncMock(
            return_value=[
                {
                    "id": "1234",
                    "name": "dummy device",
                    "type": "CastAudio",
                }
            ]
        )
        self.mock_account.async_playback_state = AsyncMock(return_value={})

        self.device_manager = DeviceManager(
            self.mock_account,
            self.mock_callack,
        )

        await self.device_manager.async_update()

    async def test_no_devices_added(self):
        self.assertEqual(len(self.device_manager.tracked_devices), 0)


class TestAlreadyTrackedDevice(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self.mock_account = MagicMock(spec=SpotifyAccount)
        self.mock_account.id = "dummy"
        self.mock_account.hass = MagicMock()
        self.mock_callack = MagicMock(spec=AddEntitiesCallback)

        self.mock_account.async_devices = AsyncMock(
            return_value=[
                {
                    "id": "1234",
                    "name": "dummy device",
                    "type": "Computer",
                }
            ]
        )
        self.mock_account.async_playback_state = AsyncMock(return_value={})

        self.device_manager = DeviceManager(
            self.mock_account,
            self.mock_callack,
        )

        self.device_manager.tracked_devices = {
            KEY: MagicMock(spec=SpotifyDevice)
        }

        await self.device_manager.async_update()

    async def test_no_devices_added(self):
        self.assertEqual(len(self.device_manager.tracked_devices), 1)

    async def test_add_entity_not_called(self):
        try:
            self.mock_callack.assert_not_called()
        except AssertionError:
            self.fail()


class TestUnavailableDevice(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self.mock_account = MagicMock(spec=SpotifyAccount)
        self.mock_account.id = "dummy"
        self.mock_account.hass = MagicMock()
        self.mock_callack = MagicMock(spec=AddEntitiesCallback)

        self.mock_account.async_devices = AsyncMock(
            return_value=[
                {
                    "id": "1234",
                    "name": "dummy device",
                    "type": "Computer",
                }
            ]
        )
        self.mock_account.async_playback_state = AsyncMock(return_value={})

        self.device_manager = DeviceManager(
            self.mock_account,
            self.mock_callack,
        )

        self.device_manager.unavailable_devices = {
            KEY: MagicMock(spec=SpotifyDevice)
        }

        self.device_manager.unavailable_devices[KEY].is_unavailable = True

        await self.device_manager.async_update()

    def test_device_added_to_tracked(self):
        self.assertIn(KEY, self.device_manager.tracked_devices)

    def test_device_was_set_to_available(self):
        self.assertFalse(
            self.device_manager.tracked_devices[KEY].is_unavailable
        )

    def test_device_removed_from_unavailable(self):
        self.assertNotIn(KEY, self.device_manager.unavailable_devices)


class TestReconnectWithNewId(IsolatedAsyncioTestCase):
    """A device that reappears with a NEW Spotify device id but the same
    name reuses the existing entity (keyed on the name) and rebinds the
    new id, instead of creating a duplicate (see #580, #586)."""

    async def asyncSetUp(self):

        self.mock_account = MagicMock(spec=SpotifyAccount)
        self.mock_account.id = "dummy"
        self.mock_account.hass = MagicMock()
        self.mock_callack = MagicMock(spec=AddEntitiesCallback)

        self.mock_account.async_devices = AsyncMock(
            return_value=[
                {
                    "id": "new-id-9999",
                    "name": "dummy device",
                    "type": "Computer",
                }
            ]
        )
        self.mock_account.async_playback_state = AsyncMock(return_value={})

        self.device_manager = DeviceManager(
            self.mock_account,
            self.mock_callack,
        )

        self.existing = MagicMock(spec=SpotifyDevice)
        self.existing.is_unavailable = True
        self.device_manager.unavailable_devices = {KEY: self.existing}
        self.device_manager.unavailable_since = {KEY: 0.0}

        await self.device_manager.async_update()

    def test_no_new_entity_created(self):
        try:
            self.mock_callack.assert_not_called()
        except AssertionError:
            self.fail()

    def test_existing_entity_reused(self):
        self.assertIs(self.device_manager.tracked_devices[KEY], self.existing)

    def test_new_device_id_rebound(self):
        self.assertEqual(
            self.existing.device_data,
            {
                "id": "new-id-9999",
                "name": "dummy device",
                "type": "Computer",
            },
        )

    def test_marked_available(self):
        self.assertFalse(self.existing.is_unavailable)


class TestCurrentlyPlayingDevice(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self.mock_account = MagicMock(spec=SpotifyAccount)
        self.mock_account.id = "dummy"
        self.mock_account.hass = MagicMock()
        self.mock_callack = MagicMock(spec=AddEntitiesCallback)

        self.mock_account.async_devices = AsyncMock(
            return_value=[
                {
                    "id": "1234",
                    "name": "dummy device",
                    "type": "Computer",
                }
            ]
        )

        self.mock_account.async_playback_state = AsyncMock(return_value={
            "device": {
                "id": "1234"
            },
            "foo": {
                "bar": "baz"
            }
        })

        self.device_manager = DeviceManager(
            self.mock_account,
            self.mock_callack,
        )

        self.device_manager.tracked_devices = {
            KEY: MagicMock(spec=SpotifyDevice)
        }
        self.device_manager.tracked_devices[KEY].id = "1234"

        await self.device_manager.async_update()

    async def test_device_playback_updated(self):
        self.device_manager.tracked_devices[KEY].playback_state = {
            "device": {
                "id": "1234",
            },
            "foo": {
                "bar": "baz",
            }
        }


class TestRemovedDevice(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self.mock_account = MagicMock(spec=SpotifyAccount)
        self.mock_account.id = "dummy"
        self.mock_account.hass = MagicMock()
        self.mock_callack = MagicMock(spec=AddEntitiesCallback)
        self.mock_device = MagicMock(spec=SpotifyDevice)
        self.mock_device.device_data = {
            "type": "Computer"
        }

        self.mock_account.async_devices = AsyncMock(return_value=[])
        self.mock_account.async_playback_state = AsyncMock()
        self.mock_account.async_playback_state.return_value = {}

        self.device_manager = DeviceManager(
            self.mock_account,
            self.mock_callack,
        )

        self.device_manager.tracked_devices = {
            KEY: self.mock_device
        }

        await self.device_manager.async_update()

    def test_device_removed_from_tracked(self):
        self.assertEqual(len(self.device_manager.tracked_devices), 0)

    def test_device_added_to_unavailable_devices(self):
        self.assertIn(KEY, self.device_manager.unavailable_devices)


class TestUnavailableEchoNotDeleted(IsolatedAsyncioTestCase):
    """Echo speakers get a new id after inactivity. They must NOT be
    deleted immediately on unavailability (which broke automations), but
    kept and reconciled/purged like any other device (see #586)."""

    async def asyncSetUp(self):

        self.mock_account = MagicMock(spec=SpotifyAccount)
        self.mock_account.id = "dummy"
        self.mock_account.hass = MagicMock()
        self.mock_callack = MagicMock(spec=AddEntitiesCallback)
        self.mock_device = MagicMock(spec=SpotifyDevice)
        self.mock_device.device_data = {
            "type": "Echo Speaker"
        }

        self.mock_account.async_devices = AsyncMock(return_value=[])
        self.mock_account.async_playback_state = AsyncMock(return_value={})

        self.device_manager = DeviceManager(
            self.mock_account,
            self.mock_callack,
        )

        self.device_manager.tracked_devices = {
            "echo_dummy": self.mock_device
        }

        await self.device_manager.async_update()

    def test_not_removed_from_hass(self):
        try:
            self.mock_device.async_remove.assert_not_called()
        except AssertionError:
            self.fail()

    def test_moved_to_unavailable(self):
        self.assertIn("echo_dummy", self.device_manager.unavailable_devices)


class TestRemovedWebPlayer(IsolatedAsyncioTestCase):

    @patch.object(DeviceManager, "remove_device")
    async def asyncSetUp(self, mock_remove):

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount),
            "callback": MagicMock(spec=AddEntitiesCallback),
            "device": MagicMock(spec=SpotifyDevice),
            "remove": mock_remove,
        }

        self.mocks["account"].id = "dummy"
        self.mocks["account"].hass = MagicMock()
        self.mocks["account"].async_devices = AsyncMock(return_value=[])
        self.mocks["account"].async_playback_state = AsyncMock()
        self.mocks["account"].async_playback_state.return_value = {}

        self.device_manager = DeviceManager(
            self.mocks["account"],
            self.mocks["callback"],
        )

        self.device_manager.tracked_devices = {
            WEB_KEY: self.mocks["device"]
        }

        self.device_manager.tracked_devices[WEB_KEY].device_data = {
            "type": "Web Player"
        }

        self.device_manager.tracked_devices[WEB_KEY].device_info = {
            "identifiers": {("spotcast", WEB_KEY)}
        }

        await self.device_manager.async_update()

    def test_device_removed_from_tracked(self):
        self.assertEqual(len(self.device_manager.tracked_devices), 0)

    def test_device_removed_from_hass(self):
        try:
            self.mocks["device"].async_remove.assert_called()
        except AssertionError:
            self.fail()

    def test_remove_device_called(self):
        try:
            self.mocks["remove"].assert_called()
        except AssertionError:
            self.fail()


class TestLegacyEntityMigration(IsolatedAsyncioTestCase):
    """On upgrade, an entity created by an older version (keyed on the
    Spotify device id) is renamed to the stable name-based unique id and
    its device registry entry is moved, instead of creating a duplicate."""

    @patch(f"{TEST_MODULE}.async_get_dr")
    @patch(f"{TEST_MODULE}.async_get_er")
    async def asyncSetUp(self, mock_er: MagicMock, mock_dr: MagicMock):

        self.entity_registry = MagicMock()
        # new unique id absent, legacy id-based unique id present
        self.entity_registry.async_get_entity_id = MagicMock(
            side_effect=[None, "media_player.dummy_device_dummy_spotcast"]
        )
        self.entity_registry.async_update_entity = MagicMock()
        mock_er.return_value = self.entity_registry

        self.device_entry = MagicMock()
        self.device_entry.id = "ha-device-id"
        self.device_registry = MagicMock()
        self.device_registry.async_get_device = MagicMock(
            side_effect=[None, self.device_entry]
        )
        self.device_registry.async_update_device = MagicMock()
        mock_dr.return_value = self.device_registry

        self.mock_account = MagicMock(spec=SpotifyAccount)
        self.mock_account.id = "dummy"
        self.mock_account.hass = MagicMock()
        self.mock_callack = MagicMock(spec=AddEntitiesCallback)

        self.mock_account.async_devices = AsyncMock(
            return_value=[
                {
                    "id": "1234",
                    "name": "dummy device",
                    "type": "Computer",
                }
            ]
        )
        self.mock_account.async_playback_state = AsyncMock(return_value={})

        self.device_manager = DeviceManager(
            self.mock_account,
            self.mock_callack,
        )

        await self.device_manager.async_update()

    def test_unique_id_migrated(self):
        try:
            self.entity_registry.async_update_entity.assert_called_once_with(
                "media_player.dummy_device_dummy_spotcast",
                new_unique_id="dummy_device_dummy_spotcast_device",
            )
        except AssertionError:
            self.fail()

    def test_device_registry_identifier_moved(self):
        try:
            self.device_registry.async_update_device.assert_called_once_with(
                "ha-device-id",
                new_identifiers={("spotcast", KEY)},
            )
        except AssertionError:
            self.fail()
