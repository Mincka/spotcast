"""Module to test the async_oauth_create_entry function"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, MagicMock, AsyncMock, call, PropertyMock

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import AbortFlow

from custom_components.spotcast.config_flow_classes.config_flow_handler \
    import (
        SpotcastFlowHandler,
        RelayedOAuth2ImplementationWithPcke,
        SOURCE_REAUTH,
        Spotify,
        ConfigEntry,
    )

from test.config_flow_classes.config_flow_handler import TEST_MODULE


class TestExternalApiEntry(IsolatedAsyncioTestCase):

    @patch.object(
        SpotcastFlowHandler,
        "_get_pcke_impl",
        new_callable=MagicMock,
    )
    @patch.object(
        SpotcastFlowHandler,
        "async_external_step",
        new_callable=MagicMock,
    )
    async def asyncSetUp(self, mock_external: AsyncMock, mock_pcke: MagicMock):

        mock_pcke.return_value = MagicMock(
            spec=RelayedOAuth2ImplementationWithPcke,
        )

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "external": mock_external,
            "pcke": mock_pcke.return_value
        }

        self.mocks["hass"].data = {}
        self.mocks["pcke"].async_generate_authorize_url = AsyncMock()
        self.mocks["pcke"].async_generate_authorize_url\
            .return_value = "https://foo.bar"

        self.handler = SpotcastFlowHandler()
        self.handler.hass = self.mocks["hass"]
        self.handler.flow_id = "12345"
        self.handler.data = {}
        await self.handler.async_oauth_create_entry({"foo": "bar"})

    def test_data_added_to_external_api(self):
        self.assertEqual(self.handler.data, {"external_api": {"foo": "bar"}})

    def test_external_step_called(self):
        try:
            self.mocks["external"].assert_called_with(
                step_id="desktop_api",
                url="https://foo.bar",
                description_placeholders={
                    "release_url": "https://github.com/Mincka/spotcast/blob/main/docs/config/spotcast_configuration.md",
                },
            )
        except AssertionError as exc:
            self.fail(exc)


class TestAllDataProvided(IsolatedAsyncioTestCase):

    @patch.object(
        SpotcastFlowHandler,
        "async_create_entry",
        new_callable=MagicMock,
    )
    @patch.object(SpotcastFlowHandler, "async_set_unique_id")
    @patch(f"{TEST_MODULE}.Spotify", new_callable=MagicMock)
    async def asyncSetUp(
        self,
        mock_spotify: MagicMock,
        mock_set_id: AsyncMock,
        mock_create: MagicMock,
    ):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "spotify_constructor": mock_spotify,
            "set_id": mock_set_id,
            "spotify_sessions": [
                MagicMock(spec=Spotify),
                MagicMock(spec=Spotify),
            ],
            "create": mock_create,
        }

        self.mocks["spotify_constructor"].side_effect = self.mocks[
            "spotify_sessions"
        ]

        self.mocks["hass"].data = {}
        self.mocks["hass"].async_add_executor_job = AsyncMock()
        self.mocks["hass"].async_add_executor_job.return_value = {
            "id": "12345",
            "display_name": "Foo Bar"
        }
        self.mocks["hass"].config_entries.async_entries.return_value = []

        self.handler = SpotcastFlowHandler()
        self.handler.hass = self.mocks["hass"]
        self.handler.flow_id = "12345"
        self.handler.context_id = "23456"
        self.handler.data = {
            "external_api": {
                "token": {
                    "access_token": "foo",
                },
            },
            "desktop_api": {
                "token": {
                    "access_token": "bar",
                },
            },
        }

        await self.handler.async_oauth_create_entry({})

    def test_spotify_created_with_public_token(self):
        # Only public token is validated during setup to avoid rate limits
        try:
            self.mocks["spotify_constructor"].assert_called_once_with(auth="foo")
        except AssertionError as exc:
            self.fail(exc)

    def test_profile_from_public_session_retrieved(self):
        # Only public session profile is retrieved during setup
        try:
            self.mocks["hass"].async_add_executor_job.assert_called_once_with(
                self.mocks["spotify_sessions"][0].current_user,
            )
        except AssertionError as exc:
            self.fail(exc)

    def test_name_set_in_data(self):
        self.assertEqual(self.handler.data["name"], "Foo Bar")

    def test_unique_id_set_to_spotify_id(self):
        try:
            self.mocks["set_id"].assert_called_with("12345")
        except AssertionError as exc:
            self.fail(exc)

    def test_entry_creation_data(self):
        try:
            self.mocks["create"].assert_called_with(
                title="Foo Bar",
                data=self.handler.data,
                options={
                    "is_default": True,
                    "base_refresh_rate": 30,
                }
            )
        except AssertionError as exc:
            self.fail(exc)


class TestProfileRefreshError(IsolatedAsyncioTestCase):

    @patch.object(SpotcastFlowHandler, "async_abort", new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.Spotify", new_callable=MagicMock)
    async def asyncSetUp(self, mock_spotify: MagicMock, mock_abort: MagicMock):

        mock_spotify.return_value = MagicMock(spec=Spotify)

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "spotify": mock_spotify.return_value,
            "abort": mock_abort,
        }

        self.handler = SpotcastFlowHandler()
        self.handler.hass = self.mocks["hass"]
        self.handler.data = {
            "external_api": {
                "token": {
                    "access_token": "foo",
                },
            },
            "desktop_api": {
                "token": {
                    "access_token": "bar",
                },
            },
        }

        self.mocks["hass"].async_add_executor_job = AsyncMock()
        self.mocks["hass"].async_add_executor_job\
            .side_effect = NotImplementedError()

        self.result = await self.handler.async_oauth_create_entry({})

    def test_process_aborted(self):
        try:
            self.mocks["abort"].assert_called_with(
                reason="connection_error",
                description_placeholders={
                    "account_type": "public",
                    "release_url": "https://github.com/Mincka/spotcast/blob/main/docs/config/spotcast_configuration.md",
                    "ticket_url": "https://github.com/Mincka/spotcast/issues/new/choose",
                },
            )
        except AssertionError as exc:
            self.fail(exc)

    def test_returns_abort_flow_result(self):
        self.assertIs(self.result, self.mocks["abort"].return_value)


# TestUnmatchedProfile removed - we no longer validate both public and private
# profiles during setup to avoid rate limit issues. Only public token is validated.


class TestReauthMismatch(IsolatedAsyncioTestCase):

    @patch.object(SpotcastFlowHandler, "source", new_callable=PropertyMock)
    @patch.object(SpotcastFlowHandler, "async_set_unique_id")
    @patch.object(
        SpotcastFlowHandler,
        "_abort_if_unique_id_mismatch",
        new_callable=MagicMock,
    )
    @patch(f"{TEST_MODULE}.Spotify", new_callable=MagicMock)
    async def test_error_raised(
        self,
        mock_spotify: MagicMock,
        mock_abort: MagicMock,
        mock_set_id: MagicMock,
        mock_source: PropertyMock,
    ):

        mock_spotify.return_value = MagicMock(spec=Spotify)

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "spotify": mock_spotify.return_value,
            "abort": mock_abort,
            "set_id": mock_set_id,
            "source": mock_source,
        }

        self.handler = SpotcastFlowHandler()
        self.mocks["source"].return_value = SOURCE_REAUTH
        self.handler.hass = self.mocks["hass"]
        self.handler.data = {
            "external_api": {
                "token": {
                    "access_token": "foo",
                },
            },
            "desktop_api": {
                "token": {
                    "access_token": "bar",
                },
            },
        }

        self.mocks["hass"].async_add_executor_job = AsyncMock()
        self.mocks["hass"].async_add_executor_job.return_value = {"id": "foo"}
        self.mocks["abort"].side_effect = AbortFlow("Dummy")

        with self.assertRaises(AbortFlow):
            await self.handler.async_oauth_create_entry({})


class TestSuccessfullReauth(IsolatedAsyncioTestCase):

    @patch.object(
        SpotcastFlowHandler,
        "_get_reauth_entry",
        new_callable=MagicMock,
    )
    @patch.object(
        SpotcastFlowHandler,
        "async_update_reload_and_abort",
        new_callable=MagicMock,
    )
    @patch.object(SpotcastFlowHandler, "source", new_callable=PropertyMock)
    @patch.object(SpotcastFlowHandler, "async_set_unique_id")
    @patch.object(
        SpotcastFlowHandler,
        "_abort_if_unique_id_mismatch",
        new_callable=MagicMock,
    )
    @patch(f"{TEST_MODULE}.Spotify", new_callable=MagicMock)
    async def asyncSetUp(
        self,
        mock_spotify: MagicMock,
        mock_abort: MagicMock,
        mock_set_id: MagicMock,
        mock_source: PropertyMock,
        mock_reload: MagicMock,
        mock_get_reauth: MagicMock,
    ):

        mock_spotify.return_value = MagicMock(spec=Spotify)

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "spotify": mock_spotify.return_value,
            "abort": mock_abort,
            "set_id": mock_set_id,
            "source": mock_source,
            "reload": mock_reload,
            "get_reauth": mock_get_reauth,
        }

        self.handler = SpotcastFlowHandler()
        self.mocks["source"].return_value = SOURCE_REAUTH
        self.handler.hass = self.mocks["hass"]
        self.handler.data = {
            "external_api": {
                "token": {
                    "access_token": "foo",
                },
            },
            "desktop_api": {
                "token": {
                    "access_token": "bar",
                },
            },
        }

        self.mocks["hass"].async_add_executor_job = AsyncMock()
        self.mocks["hass"].async_add_executor_job.return_value = {"id": "foo"}

        self.result = await self.handler.async_oauth_create_entry({})

    def test_reload_called(self):
        try:
            self.mocks["reload"].assert_called_with(
                self.mocks["get_reauth"].return_value,
                title="foo",
                data=self.handler.data,
            )
        except AssertionError as exc:
            self.fail(exc)

    def test_reauth_flow_result_returned(self):
        self.assertIs(self.result, self.mocks["reload"].return_value)
