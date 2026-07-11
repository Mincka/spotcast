"""The IsDefaultBonarySensor object

Classes
    - IsDefaultBinarySensor
"""

from logging import getLogger

from homeassistant.const import STATE_OFF, STATE_ON, EntityCategory

from custom_components.spotcast.binary_sensor.abstract_binary_sensor import (
    SpotcastBinarySensor
)

LOGGER = getLogger(__name__)


class IsDefaultBinarySensor(SpotcastBinarySensor):
    """Diagnostic binary sensor that confirms if the account is the
    default Spotcast account

    Methods:
        - _update_from_coordinator
        - _handle_update_failure
    """

    GENERIC_NAME = "Default Account"
    GENERIC_ID = "is_default_account"
    ICON = "mdi:account-check"
    ICON_OFF = ICON
    ENTITY_CATEGORY = EntityCategory.DIAGNOSTIC

    @property
    def available(self) -> bool:
        """The sensor relies on local data and is always available."""
        return True

    def _update_from_coordinator(self):
        """Updates based on the is_default property of the account"""
        LOGGER.debug(
            "Updating default state sensor for `%s`",
            self.account.entry_id,
        )

        self._attr_state = STATE_ON if self.account.is_default else STATE_OFF

    def _handle_update_failure(self):
        """Keeps reporting the local data on coordinator failure."""
        self._update_from_coordinator()
