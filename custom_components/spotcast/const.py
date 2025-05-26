"""Module for global constants.

Constants:
    DOMAIN(str): name of the integration domain
    SPOTIFY_CLIENT_ID(str): the client id for the spotify desktop oauth
        app
    DEFAULT_OPTIONS(OptionData): set of defaults for options
"""

from .entry_data import OptionData

DOMAIN = "spotcast"
SPOTIFY_CLIENT_ID = "65b708073fc0480ea92a077233ca87bd"
SPOTIFY_AUTHORIZE_URL = "https://accounts.spotify.com/en/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
DEFAULT_OPTIONS: OptionData = {
    "is_default": False,
    "base_refresh_rate": 30,
}
