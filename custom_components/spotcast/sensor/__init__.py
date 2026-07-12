"""Platform for sensor integration.

Functions:
    - async_setup_entry
"""

from logging import getLogger

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.spotcast.const import DOMAIN
from custom_components.spotcast.coordinator import SpotcastCoordinator
from custom_components.spotcast.sensor.spotify_devices_sensor import (
    SpotifyDevicesSensor,
)
from custom_components.spotcast.sensor.spotify_playlists_sensor import (
    SpotifyPlaylistsSensor,
)
from custom_components.spotcast.sensor.spotify_profile_sensor import (
    SpotifyProfileSensor,
)
from custom_components.spotcast.sensor.spotify_liked_songs_sensor import (
    SpotifyLikedSongsSensor
)
from custom_components.spotcast.sensor.spotify_product_sensor import (
    SpotifyProductSensor
)
from custom_components.spotcast.sensor.spotify_followers_sensor import (
    SpotifyFollowersSensor
)
from custom_components.spotcast.sensor.spotify_account_type_sensor import (
    SpotifyAccountTypeSensor
)
from custom_components.spotcast.sensor.spotify_current_context_sensor import (
    SpotifyCurrentContextSensor
)

LOGGER = getLogger(__name__)
SENSORS = (
    SpotifyDevicesSensor,
    SpotifyProfileSensor,
    SpotifyPlaylistsSensor,
    SpotifyLikedSongsSensor,
    SpotifyProductSensor,
    SpotifyFollowersSensor,
    SpotifyAccountTypeSensor,
    SpotifyCurrentContextSensor,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:

    coordinator: SpotcastCoordinator = (
        hass.data[DOMAIN][entry.entry_id]["coordinator"]
    )
    account = coordinator.account

    built_sensors = []

    for sensor in SENSORS:

        LOGGER.debug(
            "Creating Sensor %s for `%s`",
            sensor.GENERIC_NAME,
            account.id
        )

        built_sensors.append(sensor(coordinator))

    async_add_entities(built_sensors)
