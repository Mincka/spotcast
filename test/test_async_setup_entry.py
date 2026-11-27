"""Module to test the async_setup_entry function"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch, AsyncMock

from requests.exceptions import (
    ConnectionError as RequestsConnectionError,
    ReadTimeout,
)
from spotipy import SpotifyException

from custom_components.spotcast.sessions.exceptions import (
    UpstreamServerNotready,
)
from custom_components.spotcast import (
    async_setup_entry,
    HomeAssistant,
    ConfigEntry,
    TokenRefreshError,
    ConfigEntryAuthFailed,
    InternalServerError,
    ConfigEntryNotReady,
    SpotcastCoordinator,
)
from custom_components.spotcast.spotify import SpotifyAccount

FULL_SCOPE_DATA = {
    "external_api": {
        "token": {"scope": " ".join(SpotifyAccount.SCOPE)},
    },
}

TEST_MODULE = "custom_components.spotcast"


class TestEntryRegistration(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_setup_websocket")
    @patch(f"{TEST_MODULE}.SpotcastCoordinator", new_callable=MagicMock)
    @patch.object(SpotifyAccount, "async_from_config_entry")
    async def asyncSetUp(
        self,
        mock_account: AsyncMock,
        mock_coordinator: MagicMock,
        mock_websocket: AsyncMock,
    ):

        mock_account.return_value = MagicMock(spec=SpotifyAccount)
        mock_coordinator.return_value = MagicMock(spec=SpotcastCoordinator)

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "account": mock_account.return_value,
            "coordinator": mock_coordinator.return_value,
            "entry": MagicMock(spec=ConfigEntry),
            "forward_entry": AsyncMock(),
            "register_service": MagicMock(),
        }

        self.mocks["hass"].data = {}
        self.mocks["entry"].entry_id = "foo"
        self.mocks["entry"].data = FULL_SCOPE_DATA
        self.mocks["entry"].options = {
            "is_default": True,
            "base_refresh_rate": 20,
            "stale_device_timeout": 7,
            "device_filter_mode": "deny",
            "device_filter_patterns": "",
        }
        self.mocks["account"].is_default = True
        self.mocks["hass"].config_entries\
            .async_forward_entry_setups = self.mocks["forward_entry"]
        self.mocks["hass"].services = MagicMock()
        self.mocks["hass"].services\
            .async_register = self.mocks["register_service"]

        self.result = await async_setup_entry(
            self.mocks["hass"],
            self.mocks["entry"],
        )

    def test_function_returns_true(self):
        self.assertTrue(self.result)

    def test_service_were_registered(self):
        try:
            self.mocks["register_service"].assert_called()
        except AssertionError:
            self.fail()

    def test_update_entry_not_called(self):
        try:
            self.mocks["hass"].config_entries.async_update_entry\
                .assert_not_called()
        except AssertionError:
            self.fail()

    def test_coordinator_first_refresh_called(self):
        try:
            self.mocks["coordinator"].async_config_entry_first_refresh\
                .assert_awaited_once()
        except AssertionError:
            self.fail()

    def test_coordinator_stored_in_hass_data(self):
        self.assertIs(
            self.mocks["hass"].data["spotcast"]["foo"]["coordinator"],
            self.mocks["coordinator"],
        )

    def test_update_listener_registered(self):
        try:
            self.mocks["entry"].add_update_listener.assert_called_once()
        except AssertionError:
            self.fail()


class TestDefaultOptionsSet(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_setup_websocket")
    @patch(f"{TEST_MODULE}.SpotcastCoordinator", new_callable=MagicMock)
    @patch.object(SpotifyAccount, "async_from_config_entry")
    async def asyncSetUp(
        self,
        mock_account: MagicMock,
        mock_coordinator: MagicMock,
        mock_websocket: AsyncMock,
    ):

        mock_account.return_value = MagicMock(spec=SpotifyAccount)
        mock_coordinator.return_value = MagicMock(spec=SpotcastCoordinator)

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "account": mock_account.return_value,
            "entry": MagicMock(spec=ConfigEntry),
            "forward_entry": AsyncMock(),
            "register_service": MagicMock(),
        }

        self.mocks["hass"].data = {}
        self.mocks["entry"].entry_id = "foo"
        self.mocks["entry"].data = FULL_SCOPE_DATA
        self.mocks["entry"].options = {
            "is_default": True,
        }
        self.mocks["account"].is_default = True
        self.mocks["hass"].config_entries\
            .async_forward_entry_setups = self.mocks["forward_entry"]
        self.mocks["hass"].services = MagicMock()
        self.mocks["hass"].services\
            .async_register = self.mocks["register_service"]

        self.result = await async_setup_entry(
            self.mocks["hass"],
            self.mocks["entry"],
        )

    def test_update_entry_was_called(self):
        try:
            self.mocks["hass"].config_entries.async_update_entry\
                .assert_called_with(
                    self.mocks["entry"],
                    options={
                        "is_default": True,
                        "base_refresh_rate": 30,
                        "stale_device_timeout": 7,
                        "device_filter_mode": "deny",
                        "device_filter_patterns": "",
                    }
            )
        except AssertionError:
            self.fail()


class TestTokensErrorAtRefresh(IsolatedAsyncioTestCase):

    @patch.object(SpotifyAccount, "async_from_config_entry")
    async def test_token_error_raised(self, mock_account: AsyncMock):

        mock_account.return_value = MagicMock(spec=SpotifyAccount)

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "account": mock_account.return_value,
            "entry": MagicMock(spec=ConfigEntry),
            "forward_entry": AsyncMock(),
            "register_service": MagicMock(),
        }

        self.mocks["account"].async_ensure_tokens_valid = AsyncMock()
        self.mocks["account"].async_ensure_tokens_valid\
            .side_effect = TokenRefreshError

        self.mocks["hass"].data = {}
        self.mocks["entry"].entry_id = "foo"
        self.mocks["entry"].data = FULL_SCOPE_DATA
        self.mocks["entry"].options = {}
        self.mocks["account"].is_default = True
        self.mocks["hass"].config_entries\
            .async_forward_entry_setups = self.mocks["forward_entry"]
        self.mocks["hass"].services = MagicMock()
        self.mocks["hass"].services\
            .async_register = self.mocks["register_service"]

        with self.assertRaises(ConfigEntryAuthFailed):
            await async_setup_entry(
                self.mocks["hass"],
                self.mocks["entry"],
            )


class TestGatewayError(IsolatedAsyncioTestCase):

    @patch.object(SpotifyAccount, "async_from_config_entry")
    async def test_token_error_raised(self, mock_account: AsyncMock):

        mock_account.return_value = MagicMock(spec=SpotifyAccount)

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "account": mock_account.return_value,
            "entry": MagicMock(spec=ConfigEntry),
            "forward_entry": AsyncMock(),
            "register_service": MagicMock(),
        }

        self.mocks["account"].async_ensure_tokens_valid = AsyncMock()
        self.mocks["account"].async_ensure_tokens_valid\
            .side_effect = InternalServerError(503, "Dummy Error")

        self.mocks["hass"].data = {}
        self.mocks["entry"].entry_id = "foo"
        self.mocks["entry"].data = FULL_SCOPE_DATA
        self.mocks["entry"].options = {}
        self.mocks["account"].is_default = True
        self.mocks["hass"].config_entries\
            .async_forward_entry_setups = self.mocks["forward_entry"]
        self.mocks["hass"].services = MagicMock()
        self.mocks["hass"].services\
            .async_register = self.mocks["register_service"]

        with self.assertRaises(ConfigEntryNotReady):
            await async_setup_entry(
                self.mocks["hass"],
                self.mocks["entry"],
            )


def build_failing_setup_mocks() -> dict:
    """Returns the mocks for a setup where building the account fails"""
    mocks = {
        "hass": MagicMock(spec=HomeAssistant),
        "entry": MagicMock(spec=ConfigEntry),
    }

    mocks["hass"].data = {}
    mocks["hass"].services = MagicMock()
    mocks["entry"].entry_id = "foo"
    mocks["entry"].data = FULL_SCOPE_DATA
    mocks["entry"].options = {}

    return mocks


class TestNetworkErrorAtAccountBuild(IsolatedAsyncioTestCase):
    """Issue #92: a timeout while HA starts left the entry in
    setup_error instead of letting HA retry it."""

    async def assert_not_ready(self, side_effect: Exception):
        mocks = build_failing_setup_mocks()

        with patch.object(
            SpotifyAccount,
            "async_from_config_entry",
            side_effect=side_effect,
        ):
            with self.assertRaises(ConfigEntryNotReady) as ctx:
                await async_setup_entry(mocks["hass"], mocks["entry"])

        self.assertIs(ctx.exception.__cause__, side_effect)
        mocks["hass"].services.async_register.assert_not_called()

    async def test_profile_read_timeout(self):
        await self.assert_not_ready(ReadTimeout(
            "HTTPSConnectionPool(host='api.spotify.com', port=443): "
            "Read timed out. (read timeout=5)"
        ))

    async def test_dns_failure(self):
        await self.assert_not_ready(RequestsConnectionError(
            "Failed to resolve 'api.spotify.com'"
        ))

    async def test_token_endpoint_unreachable(self):
        await self.assert_not_ready(UpstreamServerNotready(
            "Server not ready for refresh"
        ))

    async def test_aiohttp_timeout(self):
        await self.assert_not_ready(TimeoutError())

    async def test_spotify_server_errors(self):
        await self.assert_not_ready(SpotifyException(
            429, -1, "url", reason="too many 502 error responses"
        ))


class TestNetworkErrorAtTokenCheck(IsolatedAsyncioTestCase):

    @patch.object(SpotifyAccount, "async_from_config_entry")
    async def test_not_ready_raised(self, mock_account: AsyncMock):
        mocks = build_failing_setup_mocks()
        mock_account.return_value = MagicMock(spec=SpotifyAccount)
        mock_account.return_value.is_default = True
        mock_account.return_value.async_ensure_tokens_valid = AsyncMock(
            side_effect=ReadTimeout("Read timed out")
        )

        with self.assertRaises(ConfigEntryNotReady):
            await async_setup_entry(mocks["hass"], mocks["entry"])


class TestPermanentHttpErrorAtAccountBuild(IsolatedAsyncioTestCase):
    """A 4xx will not clear on a retry, so it must not loop through
    ConfigEntryNotReady."""

    @patch.object(SpotifyAccount, "async_from_config_entry")
    async def test_error_propagates(self, mock_account: AsyncMock):
        error = SpotifyException(403, -1, "Forbidden")
        mock_account.side_effect = error
        mocks = build_failing_setup_mocks()

        with self.assertRaises(SpotifyException) as ctx:
            await async_setup_entry(mocks["hass"], mocks["entry"])

        self.assertIs(ctx.exception, error)
        self.assertNotIsInstance(ctx.exception, ConfigEntryNotReady)


class TestTokensErrorAtAccountBuild(IsolatedAsyncioTestCase):

    @patch.object(SpotifyAccount, "async_from_config_entry")
    async def test_token_error_raised(self, mock_account: AsyncMock):

        mock_account.side_effect = TokenRefreshError

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "account": mock_account.return_value,
            "entry": MagicMock(spec=ConfigEntry),
            "forward_entry": AsyncMock(),
            "register_service": MagicMock(),
        }

        self.mocks["account"].async_ensure_tokens_valid = AsyncMock()
        self.mocks["account"].async_ensure_tokens_valid\
            .side_effect = TokenRefreshError

        self.mocks["hass"].data = {}
        self.mocks["entry"].entry_id = "foo"
        self.mocks["entry"].data = FULL_SCOPE_DATA
        self.mocks["entry"].options = {}
        self.mocks["account"].is_default = True
        self.mocks["hass"].config_entries\
            .async_forward_entry_setups = self.mocks["forward_entry"]
        self.mocks["hass"].services = MagicMock()
        self.mocks["hass"].services\
            .async_register = self.mocks["register_service"]

        with self.assertRaises(ConfigEntryAuthFailed):
            await async_setup_entry(
                self.mocks["hass"],
                self.mocks["entry"],
            )
