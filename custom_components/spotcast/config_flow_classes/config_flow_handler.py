"""Module containing the Config Flow Handler for Spotcast.

Classes:
    SpotcastFlowHandler
"""

from logging import getLogger
from typing import Any, TYPE_CHECKING
from urllib.parse import urlsplit, parse_qs

from homeassistant.config_entries import CONN_CLASS_CLOUD_POLL
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import BooleanSelector
from homeassistant.helpers.config_entry_oauth2_flow import _decode_jwt
from homeassistant.components.spotify.config_flow import SpotifyFlowHandler
from homeassistant.config_entries import (
    ConfigFlowResult,
    ConfigEntry,
    SOURCE_REAUTH,
)
import voluptuous as vol
from spotipy import Spotify

from custom_components.spotcast.const import (
    DOMAIN,
    SPOTIFY_CLIENT_ID,
    SPOTIFY_AUTHORIZE_URL,
    SPOTIFY_TOKEN_URL,
)

from custom_components.spotcast.entry_data import TokenData
from custom_components.spotcast.spotify import SpotifyAccount
from custom_components.spotcast.sessions.oauth_pcke_implementation import (
    RelayedOAuth2ImplementationWithPcke,
)

from .options_flow_handler import (
    SpotcastOptionsFlowHandler,
)

if TYPE_CHECKING:  # pragma: no cover
    from custom_components.spotcast.entry_data import EntryData

LOGGER = getLogger(__name__)

_RELEASE_URL = (
    "https://github.com/Mincka/spotcast/blob/main/docs/config/"
    "spotcast_configuration.md"
)
_TICKET_URL = "https://github.com/Mincka/spotcast/issues/new/choose"
_SETUP_GUIDE_URL = (
    "https://github.com/Mincka/spotcast/blob/main/docs/config/"
    "spotcast_configuration.md"
)

# The redirect uri registered for the Spotify desktop client. The manual
# authentication path asks the user to paste the browser URL that lands
# on it after authorizing.
_DESKTOP_REDIRECT_URI = "http://127.0.0.1:8080/login"


class ManualAuthError(Exception):
    """Raised when a pasted desktop-authentication URL cannot be used.

    Attributes:
        error_key(str): the translation key of the error to show on the
            form.
    """

    def __init__(self, error_key: str):
        super().__init__(error_key)
        self.error_key = error_key


# `is_matching` only serves discovery flows (dhcp/zeroconf), which
# spotcast does not implement.
class SpotcastFlowHandler(  # pylint: disable=abstract-method
    SpotifyFlowHandler,
    domain=DOMAIN,
):
    """Handler of the Config Flow for Spotcast.

    Attributes:
        data(dict): The set of information currently collected for
            the entry

    Constants:
        - DOMAIN(str): The domain of flow is linked to
        - VERSION(int): The major version of the config
        - MINOR_VERSION(int): the minor version of the config
        - CONNECTION_CLASS(str): The type of integration being setup

    Properties:
        - extra_authorize_data(dict[str]): Provides additional
            information required for the OAuth authorisation

    Methods:
        - async_oauth_create_entry
        - async_step_reauth_confirm

    Functions:
        - async_get_options_flow
    """

    DOMAIN = DOMAIN
    VERSION = 2
    MINOR_VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

    DESKTOP_API_SCHEMA = vol.Schema(
        {
            vol.Required("access_token", default=""): cv.string,
            vol.Required("refresh_token", default=""): cv.string,
        }
    )

    DOCUMENTATION_SCHEMA = vol.Schema(
        {
            vol.Required("confirmed", default=False): BooleanSelector(),
        }
    )

    MANUAL_AUTH_SCHEMA = vol.Schema(
        {
            vol.Required("pasted_url"): cv.string,
        }
    )

    def __init__(self):
        """Constructor of the Spotcast Config Flow."""
        super().__init__()
        self.data: EntryData = {
            "name": "",
            "version": self.version,
        }
        self._pcke_impl = None
        self._manual_auth_url = None

    @property
    def version(self) -> str:
        """The active configuration version."""
        return f"{self.VERSION}.{self.MINOR_VERSION}"

    @property
    def extra_authorize_data(self) -> dict[str]:
        """Extra data to append to authorization url."""
        return {"scope": ",".join(SpotifyAccount.SCOPE)}

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Create an entry for the flow."""
        return self.async_show_form(
            step_id="doc_confirm",
            data_schema=self.DOCUMENTATION_SCHEMA,
            description_placeholders={"setup_guide": _SETUP_GUIDE_URL},
        )

    async def async_step_doc_confirm(
        self,
        user_input: dict[str, Any],
    ) -> ConfigFlowResult:
        """Entry flow to validate the user read teh documentation."""
        if user_input is None or not user_input.get("confirmed", False):
            return self.async_show_form(
                step_id="doc_confirm",
                data_schema=self.DOCUMENTATION_SCHEMA,
                errors={"confirmed": "must_confirm"},
                description_placeholders={"setup_guide": _SETUP_GUIDE_URL},
            )

        return await self.async_step_pick_implementation()

    async def async_get_desktop_token(self, external_data: dict) -> TokenData:
        """Retrives a fresh access_token from spotify dekstop app."""
        pcke_impl = self._get_pcke_impl()
        return await pcke_impl.async_resolve_external_data(external_data)

    async def async_step_desktop_api(
        self, user_input: dict[str]
    ) -> ConfigFlowResult:
        """Manages the data entry from the internal api step."""
        LOGGER.debug("Adding desktop api to entry data")

        self.data["desktop_api"] = {
            "token": await self.async_get_desktop_token(user_input),
        }

        return self.async_external_step_done(next_step_id="desktop_api_done")

    async def async_step_desktop_api_done(
        self,
        user_input: dict,
    ) -> ConfigFlowResult:
        """Passes the external steps result to oauth create entry."""
        return await self.async_oauth_create_entry(user_input)

    async def async_step_desktop_auth(
        self,
        _user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Lets the user choose how to provide the desktop token."""
        return self.async_show_menu(
            step_id="desktop_auth",
            menu_options=["desktop_api_manual", "desktop_api_auto"],
        )

    async def async_step_desktop_api_auto(
        self,
        _user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Automatic path: a local relay server redirects the browser
        back to Home Assistant to complete the authorization."""
        pkce_impl = self._get_pcke_impl()
        url = await pkce_impl.async_generate_authorize_url(
            flow_id=self.flow_id
        )

        LOGGER.debug("External Step - url `%s`", url)

        return self.async_external_step(
            step_id="desktop_api",
            url=url,
            description_placeholders={"release_url": _RELEASE_URL},
        )

    async def async_step_desktop_api_manual(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manual path: the user opens the authorization url, then pastes
        the browser url it redirects to (which fails to load) so Spotcast
        can exchange the authorization code itself. No relay needed."""
        if self._manual_auth_url is None:
            pkce_impl = self._get_pcke_impl()
            self._manual_auth_url = (
                await pkce_impl.async_generate_authorize_url(
                    flow_id=self.flow_id
                )
            )

        placeholders = {"authorize_url": self._manual_auth_url}

        if user_input is None:
            return self.async_show_form(
                step_id="desktop_api_manual",
                data_schema=self.MANUAL_AUTH_SCHEMA,
                description_placeholders=placeholders,
            )

        try:
            external_data = self._parse_pasted_redirect(
                user_input["pasted_url"]
            )
        except ManualAuthError as exc:
            return self.async_show_form(
                step_id="desktop_api_manual",
                data_schema=self.MANUAL_AUTH_SCHEMA,
                description_placeholders=placeholders,
                errors={"base": exc.error_key},
            )

        try:
            self.data["desktop_api"] = {
                "token": await self.async_get_desktop_token(external_data),
            }
        except Exception:  # pylint: disable=W0718
            LOGGER.exception("Failed to exchange the pasted authorization code")
            return self.async_show_form(
                step_id="desktop_api_manual",
                data_schema=self.MANUAL_AUTH_SCHEMA,
                description_placeholders=placeholders,
                errors={"base": "token_request_failed"},
            )

        return await self.async_oauth_create_entry({})

    def _parse_pasted_redirect(self, pasted_url: str) -> dict:
        """Parses a pasted redirect url into the OAuth external data.

        Raises:
            ManualAuthError: when the url is missing, malformed, denied,
                or carries a state that does not match this flow.
        """
        query = parse_qs(urlsplit(pasted_url.strip()).query)

        if not query:
            raise ManualAuthError("invalid_url")

        if "error" in query:
            raise ManualAuthError("access_denied")

        code = query.get("code", [None])[0]
        state = query.get("state", [None])[0]

        if code is None:
            raise ManualAuthError("missing_code")

        decoded_state = _decode_jwt(self.hass, state) if state else None

        if (
            decoded_state is None
            or decoded_state.get("flow_id") != self.flow_id
        ):
            raise ManualAuthError("invalid_state")

        return {"code": code, "state": decoded_state}

    def _get_pcke_impl(self) -> RelayedOAuth2ImplementationWithPcke:
        """Provide the custom spotcast Pkce oauth implementation."""
        if self._pcke_impl is None:
            self._pcke_impl = RelayedOAuth2ImplementationWithPcke(
                hass=self.hass,
                domain=f"{self.DOMAIN}-desktop",
                client_id=SPOTIFY_CLIENT_ID,
                authorize_url=SPOTIFY_AUTHORIZE_URL,
                token_url=SPOTIFY_TOKEN_URL,
            )

        return self._pcke_impl

    async def async_oauth_create_entry(
        self,
        data: dict[str, Any],
    ) -> ConfigFlowResult:
        """Create an entry for Spotify."""
        if "external_api" not in self.data:
            LOGGER.debug("Adding external api to entry data")
            self.data["external_api"] = data

        if "desktop_api" not in self.data:
            return await self.async_step_desktop_auth()

        external_api = self.data["external_api"]

        try:
            # Only validate the public token - desktop token was just obtained
            # via OAuth so we know it's valid. Skip desktop validation to avoid
            # rate limit issues (Desktop client_id has stricter API limits).
            public_client = Spotify(auth=external_api["token"]["access_token"])
            current_user = await self.hass.async_add_executor_job(
                public_client.current_user
            )

        except Exception:  # pylint: disable=W0718
            return self.async_abort(
                reason="connection_error",
                description_placeholders={
                    "account_type": "public",
                    "release_url": _RELEASE_URL,
                    "ticket_url": _TICKET_URL,
                },
            )

        external_api["id"] = current_user["id"]
        name = current_user.get("display_name", current_user["id"])

        self.data["name"] = name

        await self.async_set_unique_id(current_user["id"])

        if self.source == SOURCE_REAUTH:
            self._abort_if_unique_id_mismatch(reason="reauth_account_mismatch")
            return self.async_update_reload_and_abort(
                self._get_reauth_entry(),
                title=name,
                data=self.data,
            )

        self._abort_if_unique_id_configured()
        current_entries = self.hass.config_entries.async_entries(DOMAIN)

        options = {
            "is_default": len(current_entries) == 0,
            "base_refresh_rate": 30,
        }

        return self.async_create_entry(
            title=name,
            data=self.data,
            options=options,
        )

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauth dialog."""
        reauth_entry = self._get_reauth_entry()
        external_api = reauth_entry.data.get("external_api", {})

        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                description_placeholders={
                    "account": external_api.get("id", "unknown account")
                },
                errors={},
            )

        # `auth_implementation` may be absent on entries created by older
        # versions with a different data layout. Falling back to the
        # implementation picker without a preselected implementation lets the
        # user recover instead of hitting a config flow 500 error.
        auth_implementation = external_api.get("auth_implementation")

        if auth_implementation is None:
            return await self.async_step_pick_implementation()

        return await self.async_step_pick_implementation(
            user_input={"implementation": auth_implementation}
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> SpotcastOptionsFlowHandler:
        """Tells Home Assistant this integration supports configuration
        options"""
        return SpotcastOptionsFlowHandler()
