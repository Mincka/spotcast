"""The SpotifyProfileSensor object

Classes:
    - SpotifyProfileSensor
"""

from logging import getLogger

from homeassistant.const import EntityCategory
from homeassistant.const import STATE_OK, STATE_PROBLEM

from custom_components.spotcast.binary_sensor.abstract_binary_sensor import (
    SpotcastBinarySensor
)

LOGGER = getLogger(__name__)


class SpotifyProfileMalfunctionBinarySensor(SpotcastBinarySensor):
    """A Home Assistant sensor reporting information about the profile
    of a Spotify Account

    Methods:
        - _update_from_coordinator
        - _handle_update_failure
    """

    GENERIC_NAME = "Spotify Profile Malfunction"
    ICON = "mdi:bug"
    ICON_OFF = "mdi:bug-check"
    INACTIVE_STATE = STATE_OK
    ENTITY_CATEGORY = EntityCategory.DIAGNOSTIC

    @property
    def available(self) -> bool:
        """Always available. The sensor reports a coordinator failure
        as a problem state instead of becoming unavailable."""
        return True

    def _update_from_coordinator(self):
        """Marks the profile healthy after a successful refresh"""
        LOGGER.debug(
            "Profile refreshed successfully for account `%s`",
            self.account.entry_id,
        )

        self._attr_state = STATE_OK

    def _handle_update_failure(self):
        """Marks the profile as malfunctioning on coordinator failure"""
        LOGGER.error(
            "Could not refresh profile for account `%s`: %s",
            self.account.entry_id,
            self.coordinator.last_exception,
        )

        self._attr_state = STATE_PROBLEM
