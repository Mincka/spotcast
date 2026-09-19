"""Module to test the async_step_auth step and the credentials check"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from aiohttp import ClientError

from custom_components.spotcast.config_flow_classes.config_flow_handler \
    import (
        SpotcastFlowHandler,
        SpotifyFlowHandler,
        async_credentials_rejected,
    )

from test.config_flow_classes.config_flow_handler import TEST_MODULE

CREDENTIALS_PANEL_URL = (
    "https://my.home-assistant.io/redirect/application_credentials/"
)
CREDENTIALS_GUIDE_URL = (
    "https://github.com/Mincka/spotcast/blob/main/docs/config/"
    "spotcast_configuration.md"
    "#changing-or-resetting-the-application-credentials"
)


def _session_answering(
    status: int,
    payload=None,
    error: Exception | None = None,
) -> MagicMock:
    """Build an aiohttp session mock whose `post` returns a response
    with the given status and json payload, or raises `error`."""
    response = MagicMock()
    response.status = status
    response.json = AsyncMock(return_value=payload)

    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=response)
    context.__aexit__ = AsyncMock(return_value=False)

    session = MagicMock()

    if error is not None:
        session.post = MagicMock(side_effect=error)
    else:
        session.post = MagicMock(return_value=context)

    return session


class TestCredentialsRejected(IsolatedAsyncioTestCase):

    async def test_invalid_client_is_rejected(self):
        session = _session_answering(400, {"error": "invalid_client"})
        self.assertTrue(
            await async_credentials_rejected(session, "id", "secret")
        )

    async def test_request_shape(self):
        session = _session_answering(400, {"error": "invalid_client"})
        await async_credentials_rejected(session, "id", "secret")

        kwargs = session.post.call_args.kwargs
        self.assertEqual(
            session.post.call_args.args[0],
            "https://accounts.spotify.com/api/token",
        )
        self.assertEqual(kwargs["data"], {"grant_type": "client_credentials"})
        # base64("id:secret")
        self.assertEqual(
            kwargs["headers"],
            {"Authorization": "Basic aWQ6c2VjcmV0"},
        )

    async def test_other_400_error_is_not_rejected(self):
        session = _session_answering(400, {"error": "invalid_request"})
        self.assertFalse(
            await async_credentials_rejected(session, "id", "secret")
        )

    async def test_success_is_not_rejected(self):
        session = _session_answering(200, {"access_token": "abc"})
        self.assertFalse(
            await async_credentials_rejected(session, "id", "secret")
        )

    async def test_server_error_is_not_rejected(self):
        session = _session_answering(503, "<html>down</html>")
        self.assertFalse(
            await async_credentials_rejected(session, "id", "secret")
        )

    async def test_rate_limit_is_not_rejected(self):
        session = _session_answering(429, {"error": "too many"})
        self.assertFalse(
            await async_credentials_rejected(session, "id", "secret")
        )

    async def test_non_dict_payload_is_not_rejected(self):
        session = _session_answering(400, "not json")
        self.assertFalse(
            await async_credentials_rejected(session, "id", "secret")
        )

    async def test_network_error_is_not_rejected(self):
        session = _session_answering(0, error=ClientError("boom"))
        self.assertFalse(
            await async_credentials_rejected(session, "id", "secret")
        )

    async def test_timeout_is_not_rejected(self):
        session = _session_answering(0, error=TimeoutError())
        self.assertFalse(
            await async_credentials_rejected(session, "id", "secret")
        )

    async def test_undecodable_payload_is_not_rejected(self):
        session = _session_answering(400, {"error": "invalid_client"})
        response = await session.post().__aenter__()
        response.json = AsyncMock(side_effect=ValueError("bad json"))
        self.assertFalse(
            await async_credentials_rejected(session, "id", "secret")
        )


class TestRejectedCredentials(IsolatedAsyncioTestCase):

    @patch.object(SpotifyFlowHandler, "async_step_auth", new_callable=AsyncMock)
    @patch(f"{TEST_MODULE}.async_credentials_rejected", new_callable=AsyncMock)
    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    @patch.object(SpotcastFlowHandler, "async_abort", new_callable=MagicMock)
    async def asyncSetUp(
            self,
            mock_abort: MagicMock,
            mock_session: MagicMock,
            mock_check: AsyncMock,
            mock_parent: AsyncMock,
    ):
        mock_check.return_value = True
        mock_abort.return_value = "abort_result"

        self.mocks = {
            "abort": mock_abort,
            "session": mock_session,
            "check": mock_check,
            "parent": mock_parent,
        }

        self.handler = SpotcastFlowHandler()
        self.handler.hass = MagicMock()
        self.handler.flow_impl = MagicMock()
        self.handler.flow_impl.client_id = "id"
        self.handler.flow_impl.client_secret = "secret"

        self.result = await self.handler.async_step_auth()

    def test_check_used_stored_credentials(self):
        self.mocks["check"].assert_called_once_with(
            self.mocks["session"].return_value,
            "id",
            "secret",
        )

    def test_flow_aborted_with_links(self):
        self.mocks["abort"].assert_called_once_with(
            reason="invalid_credentials",
            description_placeholders={
                "credentials_url": CREDENTIALS_PANEL_URL,
                "credentials_guide": CREDENTIALS_GUIDE_URL,
            },
        )
        self.assertEqual(self.result, "abort_result")

    def test_parent_not_called(self):
        self.mocks["parent"].assert_not_called()


class TestAcceptedCredentials(IsolatedAsyncioTestCase):

    @patch.object(SpotifyFlowHandler, "async_step_auth", new_callable=AsyncMock)
    @patch(f"{TEST_MODULE}.async_credentials_rejected", new_callable=AsyncMock)
    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    @patch.object(SpotcastFlowHandler, "async_abort", new_callable=MagicMock)
    async def asyncSetUp(
            self,
            mock_abort: MagicMock,
            mock_session: MagicMock,
            mock_check: AsyncMock,
            mock_parent: AsyncMock,
    ):
        mock_check.return_value = False
        mock_parent.return_value = "external_step"

        self.mocks = {
            "abort": mock_abort,
            "session": mock_session,
            "check": mock_check,
            "parent": mock_parent,
        }

        self.handler = SpotcastFlowHandler()
        self.handler.hass = MagicMock()
        self.handler.flow_impl = MagicMock()
        self.handler.flow_impl.client_id = "id"
        self.handler.flow_impl.client_secret = "secret"

        self.result = await self.handler.async_step_auth()

    def test_parent_called(self):
        self.mocks["parent"].assert_called_once_with(None)
        self.assertEqual(self.result, "external_step")

    def test_session_taken_from_hass(self):
        self.mocks["session"].assert_called_once_with(self.handler.hass)

    def test_not_aborted(self):
        self.mocks["abort"].assert_not_called()


class TestCallbackFromSpotify(IsolatedAsyncioTestCase):
    """The second call carries the external data and must not check
    the credentials again."""

    @patch.object(SpotifyFlowHandler, "async_step_auth", new_callable=AsyncMock)
    @patch(f"{TEST_MODULE}.async_credentials_rejected", new_callable=AsyncMock)
    async def asyncSetUp(self, mock_check: AsyncMock, mock_parent: AsyncMock):
        self.mocks = {"check": mock_check, "parent": mock_parent}

        self.handler = SpotcastFlowHandler()
        self.handler.flow_impl = MagicMock()
        self.handler.flow_impl.client_id = "id"
        self.handler.flow_impl.client_secret = "secret"

        await self.handler.async_step_auth({"code": "abc", "state": "xyz"})

    def test_check_skipped(self):
        self.mocks["check"].assert_not_called()

    def test_parent_called_with_external_data(self):
        self.mocks["parent"].assert_called_once_with(
            {"code": "abc", "state": "xyz"}
        )


class TestImplementationWithoutSecret(IsolatedAsyncioTestCase):

    @patch.object(SpotifyFlowHandler, "async_step_auth", new_callable=AsyncMock)
    @patch(f"{TEST_MODULE}.async_credentials_rejected", new_callable=AsyncMock)
    async def asyncSetUp(self, mock_check: AsyncMock, mock_parent: AsyncMock):
        self.mocks = {"check": mock_check, "parent": mock_parent}

        self.handler = SpotcastFlowHandler()
        self.handler.flow_impl = MagicMock(spec=[])

        await self.handler.async_step_auth()

    def test_check_skipped(self):
        self.mocks["check"].assert_not_called()

    def test_parent_called(self):
        self.mocks["parent"].assert_called_once_with(None)


class TestFirstScreenLinks(IsolatedAsyncioTestCase):

    @patch.object(SpotcastFlowHandler, "async_show_form", new_callable=MagicMock)
    async def asyncSetUp(self, mock_form: MagicMock):
        self.mocks = {"form": mock_form}
        self.handler = SpotcastFlowHandler()
        await self.handler.async_step_user()

    def test_credentials_guide_linked(self):
        kwargs = self.mocks["form"].call_args.kwargs
        self.assertEqual(kwargs["step_id"], "doc_confirm")
        self.assertEqual(
            kwargs["description_placeholders"]["credentials_guide"],
            CREDENTIALS_GUIDE_URL,
        )
