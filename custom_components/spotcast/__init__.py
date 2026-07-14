"""Spotcast Integration - Chromecast to Spotify integrator

Functions:
    - async_setup_entry
    - async_update_options

Constants:
    - PLATFORMS(list): List of platforms implemented in this
        integration
    - DOMAIN(str): name of the domain of the integration
"""

from datetime import timedelta
from logging import getLogger

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.const import Platform
from homeassistant.helpers.device_registry import DeviceEntry

from .const import DOMAIN
from .services import ServiceHandler
from .services.const import SERVICE_SCHEMAS
from .sessions.exceptions import TokenRefreshError, InternalServerError
from .utils import ensure_default_data
from .websocket import async_setup_websocket
from .config_flow import DEFAULT_OPTIONS
from .spotify import SpotifyAccount
from .coordinator import SpotcastCoordinator

__version__ = "6.5.3-beta.6"


LOGGER = getLogger(__name__)
PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.MEDIA_PLAYER,
]


def get_missing_scopes(entry: ConfigEntry) -> set[str]:
    """Returns the required OAuth scopes missing from the entry's
    public token. OAuth scopes are frozen at consent time, so a scope
    added in a newer release is absent from tokens authorized before
    it and the account must reauthenticate to grant it.
    """
    token = entry.data.get("external_api", {}).get("token", {})
    granted = token.get("scope")

    if not granted:
        # No scope information available. Assume valid rather than
        # locking the account out.
        return set()

    granted_scopes = set(granted.replace(",", " ").split())
    return set(SpotifyAccount.SCOPE) - granted_scopes


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Initial setup of spotcast.

    Returns:
        bool: returns `True` if the integration setup was successfull
    """
    # ensure default options
    updated_options = DEFAULT_OPTIONS | entry.options

    if updated_options != entry.options:
        hass.config_entries.async_update_entry(entry, options=updated_options)

    missing_scopes = get_missing_scopes(entry)

    if missing_scopes:
        raise ConfigEntryAuthFailed(
            "The Spotify authorization is missing the required scopes "
            f"`{', '.join(sorted(missing_scopes))}`. Reauthenticate the "
            "account to grant the new permissions."
        )

    try:
        account = await SpotifyAccount.async_from_config_entry(
            hass=hass,
            entry=entry,
        )

        LOGGER.info(
            "Loaded spotify account `%s`. Set as default: %s",
            account.id,
            account.is_default,
        )

        await account.async_ensure_tokens_valid()

    except TokenRefreshError as exc:
        raise ConfigEntryAuthFailed() from exc
    except InternalServerError as exc:
        raise ConfigEntryNotReady(f"{exc.code} - {exc.message}") from exc

    coordinator = SpotcastCoordinator(hass, entry, account)
    await coordinator.async_config_entry_first_refresh()

    ensure_default_data(hass, entry.entry_id)
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    service_handler = ServiceHandler(hass)

    for service, schema in SERVICE_SCHEMAS.items():
        LOGGER.debug("Registering service %s.%s", DOMAIN, service)

        hass.services.async_register(
            domain=DOMAIN,
            service=service,
            service_func=service_handler.async_relay_service_call,
            schema=schema,
        )

    await async_setup_websocket(hass)

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry):
    """Applies a config entry update to the loaded account and
    coordinator.

    Registered as the entry update listener. Keeps the account
    options and the coordinator update interval in sync with the
    entry options without requiring a reload.

    Args:
        hass(HomeAssistant): The Home Assistant Instance
        entry(ConfigEntry): The config entry that was updated
    """
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id)

    if entry_data is None:
        return

    account = entry_data.get("account")
    coordinator = entry_data.get("coordinator")

    options = DEFAULT_OPTIONS | entry.options
    refresh_rate = options["base_refresh_rate"]

    if account is not None:
        account.is_default = options["is_default"]
        account.base_refresh_rate = refresh_rate

    device_manager = entry_data.get("device_manager")

    if device_manager is not None:
        device_manager.apply_device_options(options)

    if coordinator is None:
        return

    new_interval = timedelta(seconds=refresh_rate)

    if coordinator.update_interval != new_interval:
        LOGGER.info(
            "Setting spotcast entry `%s` to a base refresh rate of %d",
            entry.entry_id,
            refresh_rate,
        )
        coordinator.update_interval = new_interval
        await coordinator.async_request_refresh()
        return

    coordinator.async_update_listeners()


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    entry: ConfigEntry,
    device_entry: DeviceEntry,
) -> bool:
    """Allows removing a device from the UI unless Spotify currently
    reports it as an available Spotify Connect device."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id) or {}
    account = entry_data.get("account")

    if account is None:
        return True

    # Device registry entries are keyed on the stable identity key
    # (name + account). Older entries may still be keyed on the raw
    # Spotify device id, so accept both for the active check.
    # local import avoids a circular import with the media_player package
    from .media_player import (  # pylint: disable=import-outside-toplevel
        SpotifyDevice,
    )

    active = {device["id"] for device in account.devices}
    active |= {
        SpotifyDevice.compute_identity_key(device["name"], account.id)
        for device in account.devices
    }

    return not any(
        identifier in active
        for domain, identifier in device_entry.identifiers
        if domain == DOMAIN
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unloads the Spotcast config entry."""
    LOGGER.info("Unloading Spotcast entry `%s`", entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if not unload_ok:
        return False

    hass.data[DOMAIN].pop(entry.entry_id, None)

    # check if no entry remaining
    if len(hass.data[DOMAIN]) == 0:
        LOGGER.info("Last Spotcast Entry removed. Unloading services")

        for service in SERVICE_SCHEMAS:
            hass.services.async_remove(DOMAIN, service)

    return True
