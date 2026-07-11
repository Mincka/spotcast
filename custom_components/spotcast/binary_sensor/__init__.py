"""Platform for binary sensor integration.

Functions:
    - async_setup_entry
"""

from logging import getLogger

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.spotcast.const import DOMAIN
from custom_components.spotcast.coordinator import SpotcastCoordinator
from custom_components.spotcast.binary_sensor\
    .spotify_profile_malfunction_sensor import (
        SpotifyProfileMalfunctionBinarySensor,
    )
from custom_components.spotcast.binary_sensor.is_default_binary_sensor import (
    IsDefaultBinarySensor,
)

LOGGER = getLogger(__name__)

BINARY_SENSORS = (
    IsDefaultBinarySensor,
    SpotifyProfileMalfunctionBinarySensor,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup for the binaries sensors for a spotcast entry

    Args:
        - hass(HomeAssistant): The Home Assistant Instance
        - entry(ConfigEntry): The config entry being setup
        - async_add_entities(AddEntitiesCallback): The function
            callback for creating binary_sensors
    """

    coordinator: SpotcastCoordinator = (
        hass.data[DOMAIN][entry.entry_id]["coordinator"]
    )
    account = coordinator.account

    built_sensors = []

    for sensor in BINARY_SENSORS:
        LOGGER.debug(
            "Creating Sensor %s for `%s`",
            sensor.GENERIC_NAME,
            account.id
        )

        built_sensors.append(sensor(coordinator))

    async_add_entities(built_sensors)
