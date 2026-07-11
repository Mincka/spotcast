"""Module to test the async_refresh_token method of the
PrivateSession"""

import json
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.spotcast.sessions.exceptions import (
    TokenRefreshError,
)

from test.sessions.private_session import TEST_MODULE, get_mocked_session

SERVER_TIME_BODY = json.dumps({"serverTime": 1_700_000_000})
TOKEN_BODY = json.dumps({
    "accessToken": "fresh-token",
    "accessTokenExpirationTimestampMs": 1_700_003_600_000,
})


def mock_response(
    status: int = 200,
    body: str = "",
    ok: bool = True,
) -> MagicMock:
    """Builds a mocked aiohttp response"""
    response = MagicMock()
    response.status = status
    response.ok = ok
    response.headers = {}
    response.text = AsyncMock(return_value=body)
    response.json = AsyncMock(return_value={})
    return response


def mock_context(item: MagicMock) -> MagicMock:
    """Wraps a mock in an async context manager"""
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=item)
    context.__aexit__ = AsyncMock(return_value=False)
    return context


class TestSuccessfulRefresh(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.ClientSession")
    async def asyncSetUp(self, mock_session_class: MagicMock):
        self.session, self.mocks = get_mocked_session()

        self.mock_client = MagicMock()
        self.mock_client.get = MagicMock(side_effect=[
            mock_context(mock_response(body=SERVER_TIME_BODY)),
            mock_context(mock_response(body=TOKEN_BODY)),
            mock_context(mock_response(body="{}")),
        ])
        mock_session_class.return_value = mock_context(self.mock_client)

        self.result = await self.session.async_refresh_token()

    def test_token_returned(self):
        self.assertEqual(
            self.result,
            {"access_token": "fresh-token", "expires_at": 1_700_003_600},
        )

    def test_token_stored_on_session(self):
        self.assertEqual(self.session.token, "fresh-token")

    def test_expiration_stored_in_seconds(self):
        self.assertEqual(self.session._expires_at, 1_700_003_600)

    def test_supervisor_marked_healthy(self):
        self.assertTrue(self.mocks["supervisor"].is_healthy)

    def test_three_requests_made(self):
        self.assertEqual(self.mock_client.get.call_count, 3)


class TestRetriesExhausted(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.ClientSession")
    async def asyncSetUp(self, mock_session_class: MagicMock):
        self.session, self.mocks = get_mocked_session()

        def bad_token_response(*_, **__):
            return mock_context(mock_response(status=403, body="{}"))

        self.mock_client = MagicMock()
        self.mock_client.get = MagicMock(side_effect=[
            mock_context(mock_response(body=SERVER_TIME_BODY)),
            bad_token_response(),
            bad_token_response(),
        ])
        mock_session_class.return_value = mock_context(self.mock_client)

    async def test_raises_after_max_retries(self):
        with self.assertRaises(TokenRefreshError):
            await self.session.async_refresh_token(max_retries=2)


class TestRetryThenSuccess(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.ClientSession")
    async def asyncSetUp(self, mock_session_class: MagicMock):
        self.session, self.mocks = get_mocked_session()

        self.mock_client = MagicMock()
        self.mock_client.get = MagicMock(side_effect=[
            mock_context(mock_response(body=SERVER_TIME_BODY)),
            mock_context(mock_response(status=403, body="{}")),
            mock_context(mock_response(body=TOKEN_BODY)),
            mock_context(mock_response(body="{}")),
        ])
        mock_session_class.return_value = mock_context(self.mock_client)

        self.result = await self.session.async_refresh_token()

    def test_token_returned_after_retry(self):
        self.assertEqual(self.result["access_token"], "fresh-token")
