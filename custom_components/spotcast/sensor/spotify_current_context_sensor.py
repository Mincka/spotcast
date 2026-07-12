"""The SpotifyCurrentContextSensor object

Classes:
    - SpotifyCurrentContextSensor
"""

from logging import getLogger

from homeassistant.const import EntityCategory

from custom_components.spotcast.sensor.abstract_sensor import SpotcastSensor

LOGGER = getLogger(__name__)


class SpotifyCurrentContextSensor(SpotcastSensor):
    """A Home Assistant sensor reporting the name of the playlist
    currently playing on a Spotify Account.

    The name is resolved through Spotify's unofficial internal endpoint,
    so it also works for editorial and algorithmic playlists that carry
    no name through the public Web API. It reports the inactive state
    when nothing is playing or the context is not a playlist.

    Methods:
        - _update_from_coordinator
    """

    GENERIC_NAME = "Spotify Current Playlist"
    ICON = "mdi:playlist-music"
    ENTITY_CATEGORY = EntityCategory.DIAGNOSTIC
    STATE_CLASS = None

    def _update_from_coordinator(self):
        """Updates the current playlist name from the coordinator data"""

        name = self.coordinator.data.get("context_name")

        if not name:
            self._attr_state = self.INACTIVE_STATE
            self._attributes = self._default_attributes
            return

        context = (
            self.coordinator.data.get("playback_state") or {}
        ).get("context") or {}

        LOGGER.debug(
            "Current playlist for account `%s` is `%s`",
            self.account.name,
            name,
        )

        self._attr_state = name
        self._attributes = {
            "context_uri": context.get("uri"),
            "context_type": context.get("type"),
        }
