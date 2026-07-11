"""Module for the abstract SpotcastEntity class."""

from abc import ABC, abstractmethod
from logging import getLogger

from homeassistant.core import callback
from homeassistant.const import STATE_UNKNOWN, STATE_OFF, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.spotcast.coordinator import SpotcastCoordinator
from custom_components.spotcast.spotify import SpotifyAccount

LOGGER = getLogger(__name__)
ENTITY_CATEGORIES = EntityCategory


class SpotcastEntity(CoordinatorEntity[SpotcastCoordinator], ABC):
    """A generic abstract Spotcast entity for Home Assistant.

    Refreshed by the account's SpotcastCoordinator instead of
    per-entity polling. Can be customized through its list of
    constants for the class. A child instance must implement the
    `icon` property and the `_update_from_coordinator` method.

    Constants:
        - GENERIC_NAME(str): The base name of the entity to use in the
            name and id of instance. Ids based on the name converts
            the name to lowercase with `_` to replace spaces.
        - GENERIC_ID(str, optional): Overwrites the default base id if
            oresents. Defaults to None,
        - PLATFORM(str): the platform of the entity
        - DEVICE_SOURCE(str, optional): Indicates where to how to load
            the device information. Options are `account` and `None`.
            Defaults to None
        - ICON(str): the icon shown with the entity. Uses a `-off`
            version of the icon for inactive state
        - ICON_OFF(str, optional): Overwrites the icon for inactive
            state. Defaults to None.
        - DEFAULT_ATTRIBUTES(dict, optional): The state of extra
            attributes at initialisation. Defaults to None.
        - INACTIVE_STATE(str, optional): Indicate the state indicating
            the entity is inactive. Defaults to `STATE_OFF`
        - ENTITY_CATEGORY(str, optional): The category of entity
            the instance is of. Defaults to None.

    Attributes:
        - account(SpotifyAccount): the account linked to the entity
        - entity_id(str): the the entity id used by the entity
        - entity_category(str): entity_category based on the
            `ENTITY_CATEGORY` constant

    Properties:
        - extra_state_attributes(dict): the extra attributes of the
            entity
        - name(str): the name of the entity
        - unique_id(str): the unique id of the entity
        - icon(str, abstract): the icon of the entity

    Methods:
        - async_added_to_hass
        - _handle_coordinator_update
        - _handle_update_failure
        - _update_from_coordinator(abstract)
    """

    GENERIC_NAME: str = "Abstract Spotcast"
    GENERIC_ID: str = None
    PLATFORM: str = None
    DEVICE_SOURCE: str = "account"
    ICON: str = "mdi:cube"
    ICON_OFF: str = None
    INACTIVE_STATE: str | int = STATE_OFF
    ENTITY_CATEGORY: str = None

    def __init__(self, coordinator: SpotcastCoordinator):
        """Constructor a Spotcast Entity from the coordinator provided.

        Args:
            coordinator(SpotcastCoordinator): the coordinator in
                charge of refreshing the entity's account
        """
        super().__init__(coordinator)
        self.account: SpotifyAccount = coordinator.account

        LOGGER.debug(
            "Loading %s sensor for %s",
            self.GENERIC_NAME,
            self.account.name,
        )

        self._attributes = self._default_attributes
        self._attr_state = STATE_UNKNOWN
        self.entity_id = (
            f"{self.PLATFORM}.spotcast_{self.account.id}_{self._generic_id}"
        )
        self._attr_device_info = self._get_device_info()
        self.entity_category = self.ENTITY_CATEGORY

    def _get_device_info(self):
        """Builds the device info for the sensor."""
        if self.DEVICE_SOURCE is None:
            return None

        if self.DEVICE_SOURCE == "account":
            return self.account.device_info

        raise ValueError(f"`{self.DEVICE_SOURCE}` is not a valid source")

    @property
    def _generic_id(self) -> str:
        """Constructs a generic id used for the entity_id."""
        if self.GENERIC_ID is None:
            id = self.GENERIC_NAME.lower()
            id = id.replace(" ", "_")
            return id

        return self.GENERIC_ID

    @property
    def _icon_off(self) -> str:
        """Returns the icon to show if the entity is inactive."""
        icon_off = self.ICON_OFF

        if icon_off is None:
            icon_off = f"{self.ICON}-off"

        return icon_off

    @property
    def extra_state_attributes(self) -> dict:
        """Returns the extra attributes of the sensor if exist."""
        return self._attributes

    @property
    def name(self) -> str:
        """Returns the name of the entity."""
        return f"Spotcast - {self.account.name} {self.GENERIC_NAME}"

    @property
    def unique_id(self) -> str:
        """Returns a unique id for the entity."""
        return f"{self.PLATFORM}.{self.account.id}_{self._generic_id}"

    @property
    def _default_attributes(self) -> dict:
        """Reconstructors default attributes.

        If no attributes exist for the sensor. None is returned
        """
        return None

    @property
    @abstractmethod
    def icon(self) -> str:
        """Returns the mdi name of the icon to show in Home Assistant."""

    @abstractmethod
    def _update_from_coordinator(self):
        """Updates the entity state from the coordinator data.

        Called after each successful coordinator refresh. Reads from
        `self.coordinator.data` or the account's cached datasets.
        """

    def _handle_update_failure(self):
        """Resets the entity state after a failed coordinator refresh."""
        self._attr_state = STATE_UNKNOWN
        self._attributes = self._default_attributes

    @callback
    def _handle_coordinator_update(self):
        """Handles updated data from the coordinator.

        The method does not deal with the specific update process of
        the sensor, but is a generic handler for states and attributes
        for all child classes. The `_update_from_coordinator` must be
        the implementation for the specific sensor.
        """
        if self.coordinator.last_update_success:
            self._update_from_coordinator()
        else:
            self._handle_update_failure()

        super()._handle_coordinator_update()

    async def async_added_to_hass(self):
        """Applies the current coordinator data when added to hass."""
        await super().async_added_to_hass()

        if self.coordinator.data is not None:
            self._handle_coordinator_update()
