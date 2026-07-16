"""Websocket Endpoint for getting categories"""

from logging import getLogger

import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from homeassistant.core import HomeAssistant
from homeassistant.components.websocket_api import ActiveConnection
from spotipy import SpotifyException

from custom_components.spotcast.spotify.utils import select_image_url
from custom_components.spotcast.websocket.utils import (
    websocket_wrapper,
    async_get_account,
)

LOGGER = getLogger(__name__)

ENDPOINT = "spotcast/categories"
SCHEMA = vol.Schema({
    vol.Required("id"): cv.positive_int,
    vol.Required("type"): ENDPOINT,
    vol.Optional("account"): cv.string,
    vol.Optional("limit"): cv.positive_int,
})


@websocket_wrapper
async def async_get_categories(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict
):
    """Gets a list playlists from an account

    Args:
        - hass(HomeAssistant): the Home Assistant Instance
        - connection(ActiveConnection): the Active Websocket connection
            object
        - msg(dict): the message received through the websocket API
    """

    account_id = msg.get("account")
    limit = msg.get("limit")

    account = await async_get_account(hass, account_id)

    try:
        raw_categories = await account.async_categories(limit=limit)
    except SpotifyException as exc:
        # Spotify removed `GET /browse/categories` (with no
        # replacement) for client ids created after 2026-02-11.
        if exc.http_status not in (403, 404, 410):
            raise

        LOGGER.warning(
            "Spotify no longer provides browse categories for this "
            "application (removed in the February 2026 API changes). "
            "Returning an empty list."
        )
        raw_categories = []

    categories = []

    for data in raw_categories:

        categories.append({
            "id": data["id"],
            "icon": select_image_url(data["icons"]),
            "name": data["name"],
        })

    connection.send_result(
        msg["id"],
        {
            "total": len(categories),
            "account": account.id,
            "categories": categories
        },
    )
