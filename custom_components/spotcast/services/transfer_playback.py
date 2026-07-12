"""Module for the transfer_playback service

Functions:
    - async_transfer_playback
"""

from logging import getLogger

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.util.read_only_dict import ReadOnlyDict
from homeassistant.exceptions import ServiceValidationError
import voluptuous as vol


from custom_components.spotcast.spotify.account import SpotifyAccount
from custom_components.spotcast.services.play_media import (
    async_play_media,
    async_track_index,
)
from custom_components.spotcast.services.utils import EXTRAS_SCHEMA
from custom_components.spotcast.utils import copy_to_dict, get_account_entry

LOGGER = getLogger(__name__)

TRANSFER_PLAYBACK_SCHEMA = vol.Schema({
    vol.Required("media_player"): cv.ENTITY_SERVICE_FIELDS,
    vol.Optional("account"): cv.string,
    vol.Optional("data"): EXTRAS_SCHEMA,
})


async def async_transfer_playback(hass: HomeAssistant, call: ServiceCall):
    """Service to start playing media

    Args:
        - hass(HomeAssistant): the Home Assistant Instance
        - call(ServiceCall): the service call data pack
    """

    # get the current playback
    account_id = call.data.get("account")

    entry = get_account_entry(hass, account_id)

    LOGGER.debug("Loading Spotify Account for User `%s`", account_id)
    account = await SpotifyAccount.async_from_config_entry(
        hass=hass,
        entry=entry
    )

    playback_state = await account.async_playback_state(force=True)
    call_data = copy_to_dict(call.data)
    call_data["data"] = call_data.get("data", {})
    last_uri_context = _get_context_uri(
        await account.async_last_playback_state()
    )

    # check if no active playback
    if playback_state == {} and last_uri_context is None:
        LOGGER.warning("No known playback state. Defaults back to liked songs")
        call_data["spotify_uri"] = account.liked_songs_uri
    elif playback_state != {}:
        call_data["spotify_uri"] = None
    else:
        call_data = await async_rebuild_playback(call_data, account)

    call.data = ReadOnlyDict(call_data)

    await async_play_media(hass, call)


def _get_context_uri(playback_state: dict) -> str:
    """Returns the uri of the playback context from the playback state
    provided. Returns None if not context exist"""
    context: dict = playback_state.get("context")

    if context is None:
        context = {}

    return context.get("uri")


async def async_rebuild_playback(
    call_data: dict,
    account: SpotifyAccount,
) -> dict:
    """Adds detail to the service call to restart the playback from
    the last known playback state

    Args:
        - call_data(dict): the data part of the service call
        - account(SpotifyAccount): the spotify account to rebuild
            playback from

    Return:
        - dict: the call_data modified with the last known state
            information
    """
    last_playback_state: dict = await account.async_last_playback_state()
    context_uri: str = last_playback_state["context"]["uri"]
    context_type: str = last_playback_state["context"]["type"]
    extras = call_data.get("data", {})

    # set the context_uri in the call_data
    call_data["spotify_uri"] = context_uri

    # set extras if not set by user
    if extras.get("repeat") is None:
        extras["repeat"] = last_playback_state["repeat_state"]

    if extras.get("shuffle") is None:
        extras["shuffle"] = last_playback_state["shuffle_state"]

    if extras.get("position") is None:
        extras["position"] = last_playback_state["progress_ms"]/1000

    # ensure modification are set in main call data
    call_data["data"] = extras

    if extras.get("offset") is not None:
        return call_data

    current_item = last_playback_state["item"]

    # set the offset according to the context type
    if context_type == "album":
        track_index = 0
        try:
            track_index = await async_track_index(account, current_item["uri"])
            track_index = track_index[1] - 1
        except ValueError:
            pass
        call_data["data"]["offset"] = track_index
    # change the context to the episode if context is show
    elif context_type == "show":
        call_data["spotify_uri"] = current_item["uri"]
        call_data["data"]["offset"] = 0
    # start the context directly at the current track's uri. This avoids
    # paginating the whole context just to compute a numeric index, which
    # is what made transfer_playback take up to a minute on large playlists
    # (see #582).
    elif context_type in ("playlist", "collection"):
        call_data["data"]["offset"] = current_item["uri"]
    elif context_type == "artist":
        call_data["data"]["offset"] = None
    else:
        call_data["data"]["offset"] = 0

    return call_data
