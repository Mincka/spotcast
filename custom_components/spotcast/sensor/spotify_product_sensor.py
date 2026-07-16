"""The SpotifyProductSensor object

Classes:
    - SpotifyProductSensor
"""

from logging import getLogger

from homeassistant.const import EntityCategory

from custom_components.spotcast.sensor.abstract_sensor import (
    SpotcastSensor,
)

LOGGER = getLogger(__name__)


class SpotifyProductSensor(SpotcastSensor):
    """A Home Assistant sensor reporting the subscription type for a
    Spotify Account

    Methods:
        - _update_from_coordinator
    """

    GENERIC_NAME = "Spotify Product"
    ICON = "mdi:account-card"
    ICON_OFF = ICON
    ENTITY_CATEGORY = EntityCategory.DIAGNOSTIC
    STATE_CLASS = None

    def _update_from_coordinator(self):
        """Updates the substription product from the coordinator data"""

        profile = self.coordinator.data["profile"]

        LOGGER.debug(
            "Account `%s` has the `%s` subscription",
            profile["id"],
            profile["product"],
        )

        self._attr_state = profile["product"]
