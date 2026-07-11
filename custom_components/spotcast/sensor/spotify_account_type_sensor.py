"""The SpotifyAccountTypeSensor object

Classes:
    - SpotifyAccountTypeSensor
"""

from logging import getLogger

from homeassistant.const import EntityCategory

from custom_components.spotcast.sensor.abstract_sensor import SpotcastSensor

LOGGER = getLogger(__name__)


class SpotifyAccountTypeSensor(SpotcastSensor):
    """A Home Assistant sensor reporting information about the type
    of Spotify Account

    Methods:
        - _update_from_coordinator
    """

    GENERIC_NAME = "Spotify Account Type"
    ICON = "mdi:account"
    ENTITY_CATEGORY = EntityCategory.DIAGNOSTIC
    STATE_CLASS = None

    def _update_from_coordinator(self):
        """Updates the account type from the coordinator data"""

        profile = self.coordinator.data["profile"]

        LOGGER.debug(
            "Type retrieve for account id `%s`", profile["id"],
        )

        self._attr_state = profile["type"]
