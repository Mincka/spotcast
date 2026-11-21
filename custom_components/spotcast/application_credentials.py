"""Application credentials and authorization server derived from spotify

Functions:
    - async_get_authorization_server
    - async_get_description_placeholders
"""

from homeassistant.components.spotify.application_credentials import (
    async_get_authorization_server,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import (
    AUTH_CALLBACK_PATH,
    async_get_redirect_uri,
)
from homeassistant.helpers.network import NoURLAvailableError, get_url

__all__ = [
    "async_get_authorization_server",
    "async_get_description_placeholders",
]

DASHBOARD_URL = "https://developer.spotify.com/dashboard"
SETUP_GUIDE_URL = (
    "https://github.com/Mincka/spotcast/blob/main/docs/config/"
    "spotcast_configuration.md#1-create-a-spotify-application"
)
UNKNOWN_HOST_REDIRECT_URI = (
    f"https://<your Home Assistant address>{AUTH_CALLBACK_PATH}"
)


def _redirect_uri(hass: HomeAssistant) -> str:
    """Return the redirect uri the Spotify app needs for this instance.

    `async_get_redirect_uri` answers with the My Home Assistant uri when
    `my` is loaded. Without it, it reads the frontend's base url from the
    current HTTP request, which the credentials dialog does not send, so
    the instance's own url is used instead, and a template as a last
    resort so the dialog always opens.
    """
    try:
        return async_get_redirect_uri(hass)
    except RuntimeError:
        pass

    try:
        return f"{get_url(hass)}{AUTH_CALLBACK_PATH}"
    except NoURLAvailableError:
        return UNKNOWN_HOST_REDIRECT_URI


async def async_get_description_placeholders(
    hass: HomeAssistant,
) -> dict[str, str]:
    """Return the placeholders of the Add application credentials dialog.

    Home Assistant stores application credentials per integration, so the
    ones entered for the official Spotify integration are never offered to
    Spotcast. The dialog says so and points to what the Spotify app needs.

    Args:
        - hass(HomeAssistant): the Home Assistant instance

    Returns:
        - dict[str, str]: the values of the dialog's placeholders
    """
    return {
        "dashboard_url": DASHBOARD_URL,
        "redirect_uri": _redirect_uri(hass),
        "setup_guide_url": SETUP_GUIDE_URL,
    }
