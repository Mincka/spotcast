"""Module for the DeviceManager that takes care of managing new
devices and unavailable ones

Classes:
    - DeviceManager
"""

from fnmatch import fnmatchcase
from logging import getLogger
from time import time

from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import async_get as async_get_dr
from homeassistant.helpers.entity_registry import (
    async_get as async_get_er,
    async_entries_for_config_entry,
    async_entries_for_device,
)
from homeassistant.helpers.storage import Store

from custom_components.spotcast.const import DOMAIN
from custom_components.spotcast.media_player import (
    SpotifyDevice,
)
from custom_components.spotcast.sessions.retry_supervisor import (
    RetrySupervisor
)
from custom_components.spotcast.spotify import SpotifyAccount


LOGGER = getLogger(__name__)


# The manager owns the full device lifecycle state (tracked, unavailable,
# purge timestamps, filter options), which is inherent to its role.
class DeviceManager:  # pylint: disable=too-many-instance-attributes
    """Entity that manages Spotify Devices as they become available
    and drop from the device list

    Attributes:
        tracked_devices(dict[str, SpotifyDevice]): A dictionary of
            all the currently tracked devices for the account. The Key
            being the id of the device

    Constants:
        IGNORE_DEVICE_TYPES(tuple[str]): A list of device type to
            ignore when creating new media_players

    Methods:
        async_update
    """
    IGNORE_DEVICE_TYPES = (
        "CastAudio",
    )

    DELETE_ON_UNAVAILABLE = (
        "Web Player",
    )

    STALE_DEVICE_TIMEOUT = 7 * 24 * 3600

    def __init__(
        self,
        account: SpotifyAccount,
        async_add_entitites: AddEntitiesCallback,
    ):

        self.tracked_devices: dict[str, SpotifyDevice] = {}
        self.unavailable_devices: dict[str, SpotifyDevice] = {}
        self.unavailable_since: dict[str, float] = {}

        self._account = account
        self.async_add_entities = async_add_entitites
        self.supervisor = RetrySupervisor()

        self.stale_device_timeout = self.STALE_DEVICE_TIMEOUT
        self.filter_mode = "deny"
        self.filter_patterns: list[str] = []

        self.orphaned_entities: dict[str, str] = {}
        self._staleness_store: Store | None = None
        self._staleness_loaded = False
        self._saved_timestamps: dict[str, float] = {}

    @property
    def staleness_store(self) -> Store:
        """Returns the store persisting device unavailability
        timestamps, creating it on first use."""
        if self._staleness_store is None:
            self._staleness_store = Store(
                self._account.hass,
                1,
                f"spotcast_{self._account.entry_id}_device_staleness",
            )

        return self._staleness_store

    def apply_device_options(self, options: dict):
        """Applies the device lifecycle and filtering options.

        Args:
            - options(dict): the resolved config entry options
        """
        self.stale_device_timeout = (
            options["stale_device_timeout"] * 24 * 3600
        )
        self.filter_mode = options["device_filter_mode"]
        self.filter_patterns = [
            pattern.strip()
            for pattern in options["device_filter_patterns"].split(",")
            if pattern.strip()
        ]

        if self.filter_mode == "allow" and not self.filter_patterns:
            LOGGER.warning(
                "Device filter for account `%s` is in allow mode with no "
                "patterns. Ignoring the filter to avoid removing every "
                "device",
                self._account.name,
            )

    def is_filtered(self, name: str) -> bool:
        """Returns True if a device name is excluded by the device
        filter options."""
        if not self.filter_patterns:
            return False

        matches = any(
            fnmatchcase(name.lower(), pattern.lower())
            for pattern in self.filter_patterns
        )

        if self.filter_mode == "allow":
            return not matches

        return matches

    async def async_update(self, _=None):
        """Refreshes the tracked devices from the Spotify API."""

        if not self.supervisor.is_ready:
            return

        try:
            current_devices = await self._account.async_devices()
            self.supervisor.is_healthy = True
            await self.async_manage_devices(current_devices)
        except self.supervisor.SUPERVISED_EXCEPTIONS as exc:
            self.supervisor.is_healthy = False
            self.supervisor.log_message(exc)

    def _key_current_devices(self, current_devices: list) -> dict:
        """Keys the devices reported by Spotify by their stable identity
        key (name + account) rather than the ephemeral Spotify device id,
        after cleaning the type and dropping ignored devices.

        Two devices sharing a name would collide on the identity key, so
        the second one keeps the Spotify device id as a disambiguator and
        falls back to the legacy per-id behaviour.
        """
        current: dict[str, dict] = {}

        for device in current_devices:
            device["type"] = self.clean_device_type(device)

            if device["type"] in self.IGNORE_DEVICE_TYPES:
                LOGGER.debug(
                    "Ignoring player `%s` of type `%s`",
                    device["name"],
                    device["type"],
                )
                continue

            if self.is_filtered(device["name"]):
                LOGGER.debug(
                    "Ignoring player `%s`: excluded by the device "
                    "filter options",
                    device["name"],
                )
                continue

            key = SpotifyDevice.compute_identity_key(
                device["name"],
                self._account.id,
            )

            if key in current and current[key]["id"] != device["id"]:
                LOGGER.warning(
                    "Two Spotify Connect devices named `%s` for account "
                    "`%s`; keeping them as separate entities",
                    device["name"],
                    self._account.name,
                )
                key = f"{key}_{device['id']}"

            current[key] = device

        return current

    async def async_manage_devices(self, current_devices: dict):
        """Adds, marks unavailable and purges devices based on the
        current device list reported by Spotify."""
        current = self._key_current_devices(current_devices)
        remove = []

        # mark no longer available devices first
        for key, device in self.tracked_devices.items():
            if key not in current:
                LOGGER.info(
                    "Marking device `%s` unavailable for account `%s`",
                    device.name,
                    self._account.name
                )
                remove.append(key)
                device.is_unavailable = True

        for key in remove:

            device = self.tracked_devices.pop(key)

            if device.device_data["type"] in self.DELETE_ON_UNAVAILABLE:
                await device.async_remove(force_remove=True)
                self.remove_device(device.device_info["identifiers"])
            else:
                self.unavailable_devices[key] = device
                self.unavailable_since[key] = time()

        for key, device in current.items():

            if key in self.tracked_devices:
                continue

            if key in self.unavailable_devices:
                LOGGER.info(
                    "Device `%s` has became available again for account `%s`",
                    device["name"],
                    self._account.name,
                )
                # rebind the device data so the (possibly new) Spotify
                # device id is picked up without creating a new entity.
                entity = self.unavailable_devices.pop(key)
                self.unavailable_since.pop(key, None)
                entity.device_data = device
                entity.is_unavailable = False
                self.tracked_devices[key] = entity
                continue

            LOGGER.info(
                "Adding New Device `%s` for account `%s`",
                device["name"],
                self._account.name,
            )
            self._migrate_legacy_entity(key, device)
            new_device = SpotifyDevice(
                self._account,
                device,
                identity_key=key,
            )
            self.tracked_devices[key] = new_device
            # the device is live again: stop aging it toward the purge
            self.unavailable_since.pop(key, None)
            self.orphaned_entities.pop(key, None)
            self.async_add_entities([new_device])

        playback_state = await self._account.async_playback_state()
        playing_id = None

        if "device" in playback_state:
            playing_id = playback_state["device"]["id"]

        for key, device in self.tracked_devices.items():
            LOGGER.debug("Updating device info for `%s`", device.name)
            device.device_data = current[key]

            if device.id == playing_id:
                LOGGER.debug("Feeding playback state to `%s`", device.name)
                device.playback_state = playback_state
            else:
                device.playback_state = {}

        await self.async_purge_stale_devices()

    def _migrate_legacy_entity(self, key: str, device: dict):
        """Migrates an entity created by an older version, keyed on the
        ephemeral Spotify device id, onto the stable identity key. This
        keeps a user's existing entity and device (and any automation
        referencing them) instead of creating a duplicate on upgrade.

        Only devices that are currently online with the same Spotify id
        as before the upgrade can be reconciled here. Devices whose id
        changed while Home Assistant was down create a fresh entity and
        the old one is cleaned up by the stale-device purge.
        """
        entity_registry = async_get_er(self._account.hass)
        new_unique_id = f"{key}_spotcast_device"

        if entity_registry.async_get_entity_id(
            "media_player", DOMAIN, new_unique_id
        ):
            return

        old_unique_id = f"{device['id']}_{self._account.id}_spotcast_device"
        entity_id = entity_registry.async_get_entity_id(
            "media_player", DOMAIN, old_unique_id
        )

        if entity_id is None:
            return

        try:
            entity_registry.async_update_entity(
                entity_id,
                new_unique_id=new_unique_id,
            )
        except ValueError:
            LOGGER.debug(
                "Could not migrate unique id for device `%s`",
                device["name"],
            )
            return

        LOGGER.info(
            "Migrated device `%s` to stable identity `%s`",
            device["name"],
            key,
        )

        # move the device registry entry onto the stable identifier while
        # keeping the same Home Assistant device id, so automations that
        # target the device keep working (see #586).
        device_registry = async_get_dr(self._account.hass)
        old_identifiers = {(DOMAIN, device["id"])}
        new_identifiers = {(DOMAIN, key)}

        if device_registry.async_get_device(new_identifiers) is not None:
            return

        device_entry = device_registry.async_get_device(old_identifiers)

        if device_entry is not None:
            device_registry.async_update_device(
                device_entry.id,
                new_identifiers=new_identifiers,
            )

    async def async_initialize(self):
        """Loads the persisted staleness data and registers entities
        restored from previous runs for stale tracking. Must run once
        before the first update."""
        await self._async_load_stale_timestamps()
        self._sweep_orphaned_entities()

    async def _async_load_stale_timestamps(self):
        """Loads the persisted unavailability timestamps once, so the
        stale purge survives Home Assistant restarts."""
        if self._staleness_loaded:
            return

        self._staleness_loaded = True
        stored = await self.staleness_store.async_load() or {}

        for key, timestamp in stored.items():
            self.unavailable_since.setdefault(key, timestamp)

    async def _async_save_stale_timestamps(self):
        """Persists the unavailability timestamps when they changed.

        No-op until the persisted data was loaded, so a save cannot
        overwrite the store with partial state.
        """
        if not self._staleness_loaded:
            return

        if self.unavailable_since == self._saved_timestamps:
            return

        self._saved_timestamps = dict(self.unavailable_since)
        await self.staleness_store.async_save(self._saved_timestamps)

    def _sweep_orphaned_entities(self):
        """Registers media player entities restored from a previous
        run whose device Spotify no longer reports, so they age toward
        the stale purge like any unavailable device."""
        entity_registry = async_get_er(self._account.hass)
        entries = async_entries_for_config_entry(
            entity_registry,
            self._account.entry_id,
        )

        suffix = "_spotcast_device"

        for entry in entries:

            if entry.domain != "media_player":
                continue

            if not entry.unique_id.endswith(suffix):
                continue

            key = entry.unique_id[:-len(suffix)]

            if key in self.tracked_devices or key in self.unavailable_devices:
                self.orphaned_entities.pop(key, None)
                continue

            self.orphaned_entities[key] = {
                "entity_id": entry.entity_id,
                "device_id": entry.device_id,
            }
            self.unavailable_since.setdefault(key, time())

    async def async_purge_stale_devices(self):
        """Removes devices that have been unavailable for longer than
        the grace period. Spotify session devices (e.g. Jams) get a
        new id every session and would otherwise accumulate forever.
        """
        now = time()

        for key in list(self.unavailable_devices):

            elapsed = now - self.unavailable_since.get(key, now)

            if elapsed < self.stale_device_timeout:
                continue

            device = self.unavailable_devices.pop(key)
            self.unavailable_since.pop(key, None)

            LOGGER.info(
                "Removing device `%s` for account `%s`. Unavailable for "
                "more than %d days",
                device.name,
                self._account.name,
                self.stale_device_timeout // 86400,
            )

            await device.async_remove(force_remove=True)

            try:
                self.remove_device(device.device_info["identifiers"])
            except KeyError:
                LOGGER.debug(
                    "Device `%s` was already absent from the registry",
                    device.name,
                )

        await self._async_purge_orphaned_entities(now)
        await self._async_save_stale_timestamps()

    async def _async_purge_orphaned_entities(self, now: float):
        """Removes registry entities restored from previous runs once
        they have been unavailable for longer than the grace period.

        The device registry entry is removed through the entity's
        device id: entities created by older versions carry legacy
        identifiers that cannot be reconstructed from the unique id.
        """
        if not self.orphaned_entities:
            return

        entity_registry = async_get_er(self._account.hass)

        for key, orphan in list(self.orphaned_entities.items()):

            elapsed = now - self.unavailable_since.get(key, now)

            if elapsed < self.stale_device_timeout:
                continue

            self.orphaned_entities.pop(key)
            self.unavailable_since.pop(key, None)

            entity_id = orphan["entity_id"]
            device_id = orphan["device_id"]

            LOGGER.info(
                "Removing restored device `%s` for account `%s`. "
                "Unavailable for more than %d days",
                entity_id,
                self._account.name,
                self.stale_device_timeout // 86400,
            )

            if entity_registry.async_get(entity_id) is not None:
                entity_registry.async_remove(entity_id)

            if device_id is None:
                continue

            if async_entries_for_device(
                entity_registry,
                device_id,
                include_disabled_entities=True,
            ):
                LOGGER.debug(
                    "Device of `%s` still has entities. Keeping it",
                    entity_id,
                )
                continue

            device_registry = async_get_dr(self._account.hass)

            if device_registry.async_get(device_id) is not None:
                device_registry.async_remove_device(device_id)
                LOGGER.info(
                    "Removed Device `%s`. No Longer reported",
                    device_id,
                )

    def remove_device(
            self,
            identifiers: set[tuple[str, str]]
    ):
        """Removes a device from the device registry"""

        device_registry = async_get_dr(self._account.hass)
        device_entry = device_registry.async_get_device(identifiers)

        if device_entry is None:
            raise KeyError(f"No device found for identifiers `{identifiers}`")

        device_registry.async_remove_device(device_entry.id)
        LOGGER.info("Removed Device `%s`. No Longer reported", device_entry.id)

    @staticmethod
    def clean_device_type(device: dict) -> str:
        """Returns a clean device type based on the device data from
        Spotify. Used to identify more specific device types requiring
        special handling"""

        device_type: str = device["type"]

        if device["name"].startswith("Web Player"):
            return "Web Player"

        if device["id"][-7:-1] == "_amzn_":
            return "Echo Speaker"

        # return the device type back if no special case found
        return device_type
