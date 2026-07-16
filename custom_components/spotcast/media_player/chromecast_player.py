"""Module containing the chromecast media player implementation"""

from logging import getLogger
from hashlib import md5

from pychromecast import Chromecast as ParentChromecast
from pychromecast.const import CAST_TYPE_GROUP

import pychromecast  # pylint: disable=unused-import

from custom_components.spotcast.media_player._abstract_player import (
    MediaPlayer
)

LOGGER = getLogger(__name__)


class Chromecast(ParentChromecast, MediaPlayer):
    """A chromecast media player

    Constants:
        - PLATFORM(str): the Home Assistant platform hosting the
            devices
        - DEVICE_TYPE(type): the type of device searched for

    Properties:
        - id: the spotify device if for the player

    functions:
        - from_hass
        - from_network
    """

    INTEGRATION = "cast"

    # Overridden with the id the device reports during the cast handshake
    # when it differs from the requested one (see the id property).
    _spotify_id: str = None

    @property
    def id(self) -> str:
        """Returns the spotify id of the player.

        Defaults to `md5(name)`, the id requested during the cast
        handshake. A non-Google speaker group can register under the group
        coordinator's id instead; once the handshake reports that id it is
        set here and becomes the playback target."""
        return self._spotify_id or md5(self.name.encode()).hexdigest()

    @id.setter
    def id(self, value: str) -> None:
        self._spotify_id = value

    @property
    def is_group(self) -> bool:
        """Returns True if the player is a speaker group (e.g. a Google
        Cast group), as opposed to a single cast device."""
        return self.cast_type == CAST_TYPE_GROUP
