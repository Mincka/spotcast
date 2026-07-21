"""Module for the spotify account class.

Classes:
    SpotifyAccount
"""

from asyncio import Lock
from functools import partial
from logging import getLogger

from spotipy import SpotifyException
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType
from homeassistant.helpers.storage import Store

from custom_components.spotcast.const import DOMAIN
from custom_components.spotcast.sessions import (
    DesktopSession,
    PublicSession,
    ConnectionSession,
    async_get_config_entry_implementation,
)
from custom_components.spotcast.utils import ensure_default_data
from custom_components.spotcast.spotify.client import Spotify
from custom_components.spotcast.spotify.dataset import Dataset
from custom_components.spotcast.spotify.search_query import SearchQuery
from custom_components.spotcast.spotify.exceptions import PlaybackError

from custom_components.spotcast.spotify.account.paging import PagingMixin
from custom_components.spotcast.spotify.account.token import TokenMixin
from custom_components.spotcast.spotify.account.profile import ProfileMixin
from custom_components.spotcast.spotify.account.library import LibraryMixin
from custom_components.spotcast.spotify.account.playback import PlaybackMixin
from custom_components.spotcast.spotify.account.internal import InternalApiMixin

LOGGER = getLogger(__name__)

# Names re-exported for callers and tests that import them from this
# module (kept importable through the facade after the split).
__all__ = [
    "SpotifyAccount",
    "PublicSession",
    "DesktopSession",
    "ConnectionSession",
    "HomeAssistant",
    "ConfigEntry",
    "Dataset",
    "Spotify",
    "SpotifyException",
    "Store",
    "PlaybackError",
    "DeviceInfo",
    "DeviceEntryType",
    "SearchQuery",
]


# The facade holds the shared instance state (sessions, apis, datasets,
# caches, stores) that every mixin operates on, so the count of instance
# attributes is inherent to it being the single owner of account state.
class SpotifyAccount(  # pylint: disable=too-many-instance-attributes
    PagingMixin,
    TokenMixin,
    ProfileMixin,
    LibraryMixin,
    PlaybackMixin,
    InternalApiMixin,
):
    """The account of a Spotify user.

    The account is assembled from focused mixins, each owning one
    responsibility: dataset/pagination infrastructure (PagingMixin),
    token and session lifecycle (TokenMixin), profile and identity
    (ProfileMixin), content and library reads (LibraryMixin), playback
    control (PlaybackMixin), and unofficial internal-endpoint reads
    (InternalApiMixin). This class holds the shared instance state they
    all operate on and the account loader.

    Attributes:
        - hass(HomeAssistant): The Home Assistance instance
        - sessions(dict[str, ConnectionSession]): A dictionary with
            both the Internal (Private) and External (Public) API
            access
        - is_default(bool): set to True if the account should be
            treated as default when calling services

    Properties:
        - id(str): the identifier of the account
        - name(str): the display name for the account
        - profile(dict): the full profile dictionary of the account
        - country(str): the country code where the account currently
            is.
        - image_link(str): the profile image image link
        - product(str): the current subscription product the user has
        - type(str): the type of account loaded
        - liked_songs_uri(str): the uri for the liked_songs playlist
        - device_info(DeviceInfo): the Home Assistant device info
        - base_refresh_rate(int): the base dataset refresh rate

    Constants:
        - SCOPE(tuple): A list of API permissions required for the
            instance to work properly
        - DJ_URI(str): the uri for the DJ playlist
        - REFRESH_RATE(int): default rate at which to deem the cache
            deprecated
        - DATASETS(dict[str, dict]): Default configuration for datasets
            used by the account
        - SESSION_CONFIG_MAP(dict[str, str]): maps each session key to
            its config entry data key

    Functions:
        - async_from_config_entry
    """

    SCOPE = (
        "user-modify-playback-state",
        "user-read-playback-state",
        "user-read-private",
        "playlist-read-private",
        "playlist-read-collaborative",
        "user-library-read",
        "user-library-modify",
        "user-top-read",
        "user-read-playback-position",
        "user-read-recently-played",
        "user-follow-read",
    )

    DJ_URI = "spotify:playlist:37i9dQZF1EYkqdzj48dyYq"
    REFRESH_RATE = 30
    DATASETS = {
        "devices": {
            "refresh_factor": 1,
            "can_expire": False,
        },
        "liked_songs": {
            "refresh_factor": 10,
            "can_expire": False,
        },
        "liked_songs_count": {
            "refresh_factor": 10,
            "can_expire": False,
        },
        "playlists": {
            "refresh_factor": 10,
            "can_expire": False,
        },
        "playlists_count": {
            "refresh_factor": 10,
            "can_expire": False,
        },
        "profile": {
            "refresh_factor": 20,
            "can_expire": True,
        },
        "categories": {
            "refresh_factor": 20,
            "can_expire": False,
        },
        "playback_state": {
            "refresh_factor": 1 / 2,
            "can_expire": False,
        },
    }

    SESSION_CONFIG_MAP = {
        "public": "external_api",
        "private": "desktop_api",
    }

    # The account facade takes both sessions and the entry settings at
    # construction, so the argument count is inherent to it.
    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        entry_id: str,
        hass: HomeAssistant,
        public_session: PublicSession,
        private_session: DesktopSession,
        is_default: bool = False,
        base_refresh_rate: int = 30,
    ):
        """The account of a Spotify user.

        Args:
            entry_id(str): The id of the config entry in HomeAssistant
                for the account.
            hass(HomeAssistant): The Home Assistant Instance
            public_session(OAuth2Session): The public api session
                for the Spotify Account
            private_session(InternalSession): The private api
                session for the Spotify Account
            is_default(bool, optional): True if account is treated as
                default for service call. Defaults to False.
            base_refresh_rate(int, optional): The base refresh rate
                used to update dateset
        """
        self.entry_id = entry_id
        self.hass = hass
        self._lock = Lock()
        self.sessions: dict[str, ConnectionSession] = {
            "public": public_session,
            "private": private_session,
        }
        self.apis: dict[str, Spotify] = {}

        for name, session in self.sessions.items():
            self.apis[name] = Spotify(
                auth=session.access_token,
                token_refresher=partial(self.get_token, name, force=True),
            )

        self.is_default = is_default
        self._base_refresh_rate = base_refresh_rate

        self._datasets: dict[str, Dataset] = {}
        self._last_playback_state = {}
        self._context_name_cache: tuple[str | None, str | None] = (None, None)
        self._playback_store = Store(
            hass,
            1,
            f"spotcast_{entry_id}_last_state",
        )

        for name, dataset in self.DATASETS.items():
            refresh_rate = dataset["refresh_factor"] * self._base_refresh_rate
            can_expire = dataset["can_expire"]
            self._datasets[name] = Dataset(name, refresh_rate, can_expire)

    @property
    def base_refresh_rate(self) -> int:
        """Returns the current base refresh rate."""
        return self._base_refresh_rate

    @base_refresh_rate.setter
    def base_refresh_rate(self, value: int):
        """Sets the base refresh rate and updates the dataset.

        Args:
            value(int): the new base refresh_rate
        """
        self._base_refresh_rate = value

        for name, dataset in self._datasets.items():
            refresh_factor = self.DATASETS[name]["refresh_factor"]
            dataset.refresh_rate = value * refresh_factor

    @staticmethod
    async def async_from_config_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> "SpotifyAccount":
        """Builds a Spotify Account from the HA config entry.

        Args:
            hass(HomeAssistant): the HomeAssistant Instance object
            entry(ConfigEntry): the config entry for the spotify
                account being setup
        Returns:
            SpotifyAccount: A spotify account from the api config in
                the config entry
        """
        hass = ensure_default_data(hass, entry.entry_id)
        domain_data = hass.data[DOMAIN]

        account = domain_data[entry.entry_id].get("account")

        if account is not None:
            LOGGER.debug(
                "Providing preexisting account for entry `%s`", entry.entry_id
            )
            return account

        oauth_implementation = await async_get_config_entry_implementation(
            hass=hass,
            config_entry=entry,
        )

        public_session = PublicSession(hass, entry, oauth_implementation)
        await public_session.async_ensure_token_valid()

        private_session = DesktopSession(hass, entry)
        await private_session.async_ensure_token_valid()

        # only pass the account level options: the entry options also
        # carry settings for other components (e.g. device filtering)
        account = SpotifyAccount(
            entry_id=entry.entry_id,
            hass=hass,
            public_session=public_session,
            private_session=private_session,
            is_default=entry.options.get("is_default", False),
            base_refresh_rate=entry.options.get("base_refresh_rate", 30),
        )

        await account.async_ensure_tokens_valid(force_entry_update=True)

        await account.async_profile()

        LOGGER.debug(
            "Adding entry `%s` to spotcast data entries",
            entry.entry_id,
        )
        hass.data[DOMAIN][entry.entry_id]["account"] = account

        return account
