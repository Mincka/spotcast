"""Token and session lifecycle handling for the Spotify account.

Classes:
    TokenMixin
"""

from asyncio import run_coroutine_threadsafe
from copy import deepcopy
import datetime as dt
from logging import getLogger

from homeassistant.config_entries import ConfigEntry, SOURCE_REAUTH

from custom_components.spotcast.sessions import ConnectionSession
from custom_components.spotcast.spotify.exceptions import TokenError

LOGGER = getLogger(__name__)


class TokenMixin:
    """Token retrieval, refresh, and session health for the account."""

    @property
    def health_status(self) -> dict[str, bool]:
        """Returns the health status of the underlying sessions."""
        health = {}

        for key, session in self.sessions.items():
            health[key] = session.is_healthy

        return health

    def get_token(self, api: str) -> str:
        """Retrives a token from the requested session.

        Args:
            api(str): The api to retrieve from. Cann be `internal`
                or `external`.

        Returns:
            str: token for the requested session
        """
        return run_coroutine_threadsafe(
            self.async_get_token(api), self.hass.loop
        ).result()

    async def async_get_token(self, api: str) -> str:
        """Retrives a token from the requested session.

        Args:
            api(str): The api to retrieve from. Can be `internal` or
                `external`.

        Returns:
            - str: token for the requested session
        """
        await self.sessions[api].async_ensure_token_valid()
        return self.sessions[api].access_token

    async def async_ensure_tokens_valid(
        self,
        skip_profile: bool = False,
        reauth_on_fail: bool = True,
        force_entry_update: bool = False,
    ):
        """Ensures the token are valid.

        Args:
            skip_profile(bool, optional): set True to skip the
                profile update. Defaults to False
            reauth_on_fail(bool, optional): Asks for reauthorisation
                of the entry on failure to get token. Defaults to True.
            force_entry_update(bool, optional): Forces the config entry
                update even if no data was updated.
        """
        if not skip_profile:
            await self.async_profile()

        async with self._lock:
            entry = self.hass.config_entries.async_get_entry(self.entry_id)
            new_data = deepcopy({**entry.data})
            need_update = False

            for key, session in self.sessions.items():
                was_updated = await self._async_refresh_single_token(
                    session,
                    reauth_on_fail,
                )

                LOGGER.debug(
                    "Session `%s` token updated: %s",
                    key,
                    was_updated,
                )

                need_update = need_update or was_updated

                new_data[self.SESSION_CONFIG_MAP[key]] = {**session.data}

                self.apis[key].set_auth(session.access_token)

            if need_update or force_entry_update:
                LOGGER.info(
                    "New information receive, updating entry for `%s`",
                    self.entry_id,
                )
                new_data["last_update"] = dt.datetime.now().isoformat()

                result = self.hass.config_entries.async_update_entry(
                    entry=entry,
                    data=new_data,
                )

                LOGGER.debug("Config Entry updated: %s", result)

    async def _async_refresh_single_token(
        self,
        session: ConnectionSession,
        reauth_on_fail: bool = True,
    ) -> bool:
        """Refreshes the token a a specific session."""
        try:
            was_updated = await session.async_ensure_token_valid()
            return was_updated
        except TokenError as exc:
            if reauth_on_fail:
                LOGGER.error(
                    "An error occured while trying to refresh the "
                    "token. Reauthentication requested"
                )

                entry = self.hass.config_entries.async_get_entry(self.entry_id)
                entry.async_start_reauth(
                    self.hass, context={"source": SOURCE_REAUTH}
                )

            raise exc

    def _request_reauth(self, entry: ConfigEntry):
        """Requests reauth for an entry."""
        entry.async_start_reauth(
            self.hass,
            context={"source": SOURCE_REAUTH},
        )
