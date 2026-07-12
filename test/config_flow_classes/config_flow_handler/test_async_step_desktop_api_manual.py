"""Module to test the async_step_desktop_api_manual step"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from homeassistant.core import HomeAssistant

from custom_components.spotcast.config_flow_classes.config_flow_handler \
    import (
        SpotcastFlowHandler,
        RelayedOAuth2ImplementationWithPcke,
    )

from test.config_flow_classes.config_flow_handler import TEST_MODULE

VALID_STATE = {
    "flow_id": "12345",
    "redirect_uri": "http://127.0.0.1:8080/login",
}


class TestFormShown(IsolatedAsyncioTestCase):

    @patch.object(
        SpotcastFlowHandler,
        "_get_pcke_impl",
        new_callable=MagicMock,
    )
    @patch.object(
        SpotcastFlowHandler,
        "async_show_form",
        new_callable=MagicMock,
    )
    async def asyncSetUp(self, mock_form: MagicMock, mock_pcke: MagicMock):

        mock_pcke.return_value = MagicMock(
            spec=RelayedOAuth2ImplementationWithPcke,
        )
        mock_pcke.return_value.async_generate_authorize_url = AsyncMock(
            return_value="https://auth.url"
        )

        self.mocks = {"form": mock_form}

        self.handler = SpotcastFlowHandler()
        self.handler.flow_id = "12345"

        await self.handler.async_step_desktop_api_manual()

    def test_form_shown_with_authorize_url(self):
        kwargs = self.mocks["form"].call_args.kwargs
        self.assertEqual(kwargs["step_id"], "desktop_api_manual")
        self.assertEqual(
            kwargs["description_placeholders"],
            {"authorize_url": "https://auth.url"},
        )


class TestHappyPath(IsolatedAsyncioTestCase):

    @patch.object(
        SpotcastFlowHandler,
        "async_oauth_create_entry",
        new_callable=AsyncMock,
    )
    @patch.object(
        SpotcastFlowHandler,
        "async_get_desktop_token",
        new_callable=AsyncMock,
    )
    @patch(f"{TEST_MODULE}._decode_jwt")
    async def asyncSetUp(
        self,
        mock_decode: MagicMock,
        mock_token: AsyncMock,
        mock_create: AsyncMock,
    ):

        mock_decode.return_value = dict(VALID_STATE)
        mock_token.return_value = {"access_token": "tok"}

        self.mocks = {
            "decode": mock_decode,
            "token": mock_token,
            "create": mock_create,
        }

        self.handler = SpotcastFlowHandler()
        self.handler.hass = MagicMock(spec=HomeAssistant)
        self.handler.flow_id = "12345"
        self.handler.data = {}
        self.handler._manual_auth_url = "https://auth.url"

        self.result = await self.handler.async_step_desktop_api_manual({
            "pasted_url": (
                "http://127.0.0.1:8080/login?code=the-code&state=the-state"
            ),
        })

    def test_token_exchanged_with_code_and_state(self):
        try:
            self.mocks["token"].assert_called_once_with(
                {"code": "the-code", "state": VALID_STATE},
            )
        except AssertionError as exc:
            self.fail(exc)

    def test_desktop_token_stored(self):
        self.assertEqual(
            self.handler.data["desktop_api"],
            {"token": {"access_token": "tok"}},
        )

    def test_oauth_create_entry_called(self):
        try:
            self.mocks["create"].assert_called_once_with({})
        except AssertionError as exc:
            self.fail(exc)

        self.assertIs(self.result, self.mocks["create"].return_value)


class _ManualErrorCase(IsolatedAsyncioTestCase):
    """Base for the error-path tests. Subclasses set PASTED, DECODE and
    TOKEN_RAISES then assert on EXPECTED_ERROR."""

    PASTED = ""
    DECODE = None
    TOKEN_RAISES = False
    EXPECTED_ERROR = ""

    async def _run(self):
        with patch.object(
            SpotcastFlowHandler, "async_show_form", new_callable=MagicMock,
        ) as mock_form, patch.object(
            SpotcastFlowHandler,
            "async_get_desktop_token",
            new_callable=AsyncMock,
        ) as mock_token, patch(
            f"{TEST_MODULE}._decode_jwt", return_value=self.DECODE,
        ):
            if self.TOKEN_RAISES:
                mock_token.side_effect = ValueError("boom")

            handler = SpotcastFlowHandler()
            handler.hass = MagicMock(spec=HomeAssistant)
            handler.flow_id = "12345"
            handler.data = {}
            handler._manual_auth_url = "https://auth.url"

            await handler.async_step_desktop_api_manual({
                "pasted_url": self.PASTED,
            })

            return mock_form.call_args.kwargs

    async def _assert_error(self):
        kwargs = await self._run()
        self.assertEqual(kwargs["errors"], {"base": self.EXPECTED_ERROR})


class TestInvalidUrl(_ManualErrorCase):
    PASTED = "not-a-url"
    EXPECTED_ERROR = "invalid_url"

    async def test_error(self):
        await self._assert_error()


class TestAccessDenied(_ManualErrorCase):
    PASTED = "http://127.0.0.1:8080/login?error=access_denied&state=x"
    EXPECTED_ERROR = "access_denied"

    async def test_error(self):
        await self._assert_error()


class TestMissingCode(_ManualErrorCase):
    PASTED = "http://127.0.0.1:8080/login?state=x"
    EXPECTED_ERROR = "missing_code"

    async def test_error(self):
        await self._assert_error()


class TestInvalidState(_ManualErrorCase):
    PASTED = "http://127.0.0.1:8080/login?code=abc&state=bad"
    DECODE = None
    EXPECTED_ERROR = "invalid_state"

    async def test_error(self):
        await self._assert_error()


class TestFlowIdMismatch(_ManualErrorCase):
    PASTED = "http://127.0.0.1:8080/login?code=abc&state=other"
    DECODE = {"flow_id": "other-flow", "redirect_uri": "x"}
    EXPECTED_ERROR = "invalid_state"

    async def test_error(self):
        await self._assert_error()


class TestTokenRequestFailed(_ManualErrorCase):
    PASTED = "http://127.0.0.1:8080/login?code=abc&state=good"
    DECODE = dict(VALID_STATE)
    TOKEN_RAISES = True
    EXPECTED_ERROR = "token_request_failed"

    async def test_error(self):
        await self._assert_error()
