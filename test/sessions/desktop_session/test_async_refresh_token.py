"""Module to test the async_refresh_token method"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch, AsyncMock

from aiohttp import ClientSession

from custom_components.spotcast.sessions.desktop_session import (
    ClientError,
    InternalServerError,
)

from test.sessions.desktop_session import get_mocked_session, TEST_MODULE


class TestSuccessfullRefresh(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.time", new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def asyncSetUp(
        self,
        mock_http_session: MagicMock,
        mock_time: MagicMock,
    ):

        mock_http_session.return_value = MagicMock(spec=ClientSession)

        self.session, self.mocks = get_mocked_session()

        self.mocks["http_session"] = mock_http_session.return_value
        self.mocks["time"] = mock_time
        self.mocks["time"].return_value = 400

        self.mocks["http_session"].post = AsyncMock()
        self.mocks["http_session"].post.return_value = MagicMock()
        self.mocks["response"] = self.mocks["http_session"].post.return_value
        self.mocks["response"].json = AsyncMock()
        self.mocks["response"].json.return_value = {
            "access_token": "foo",
            "refresh_token": "bar",
            "expires_in": 100,
            "scope": "read write",
        }
        self.mocks["response"].status = 200

        self.result = await self.session.async_refresh_token()

    def test_token_data(self):
        self.assertEqual(
            self.result,
            {
                "access_token": "foo",
                "refresh_token": "bar",
                "expires_at": 500,
                "scope": "read write",
            }
        )


class TestRefreshWithoutNewRefreshToken(IsolatedAsyncioTestCase):
    """Spotify may omit `refresh_token` when the current one stays
    valid. The session must keep it instead of dropping it."""

    @patch(f"{TEST_MODULE}.time", new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def asyncSetUp(
        self,
        mock_http_session: MagicMock,
        mock_time: MagicMock,
    ):

        mock_http_session.return_value = MagicMock(spec=ClientSession)

        self.session, self.mocks = get_mocked_session()

        self.mocks["http_session"] = mock_http_session.return_value
        self.mocks["time"] = mock_time
        self.mocks["time"].return_value = 400

        self.mocks["http_session"].post = AsyncMock()
        self.mocks["http_session"].post.return_value = MagicMock()
        self.mocks["response"] = self.mocks["http_session"].post.return_value
        self.mocks["response"].json = AsyncMock()
        self.mocks["response"].json.return_value = {
            "access_token": "baz",
            "expires_in": 100,
            "scope": "read write",
        }
        self.mocks["response"].status = 200

        self.result = await self.session.async_refresh_token()

    def test_refresh_token_retained(self):
        self.assertEqual(
            self.result,
            {
                "access_token": "baz",
                "refresh_token": "bar",
                "expires_at": 500,
                "scope": "read write",
            }
        )


class TestStandardFormatErrorMessage(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.LOGGER", new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.time", new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def test_error_raised(
        self,
        mock_http_session: MagicMock,
        mock_time: MagicMock,
        mock_logger: MagicMock,
    ):

        mock_http_session.return_value = MagicMock(spec=ClientSession)

        self.session, self.mocks = get_mocked_session()

        self.mocks["http_session"] = mock_http_session.return_value
        self.mocks["time"] = mock_time
        self.mocks["logger"] = mock_logger

        self.mocks["time"].return_value = 400

        self.mocks["http_session"].post = AsyncMock()
        self.mocks["http_session"].post.return_value = MagicMock()
        self.mocks["response"] = self.mocks["http_session"].post.return_value
        self.mocks["response"].json = AsyncMock()
        self.mocks["response"].json.return_value = {
            "error": "Dummy",
            "error_description": "Dummy Error"
        }
        self.mocks["response"].status = 400
        self.mocks["response"].raise_for_status.side_effect = ClientError()

        with self.assertRaises(ClientError):
            self.result = await self.session.async_refresh_token()

        try:
            self.mocks["logger"].error.assert_called_with(
                "Token request for %s failed with status %s (%s): %s",
                "spotcast",
                400,
                "Dummy",
                "Dummy Error",
            )
        except AssertionError as exc:
            self.fail(exc)


class TestUnkownFormatErrorMessage(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.LOGGER", new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.time", new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def test_error_raised(
        self,
        mock_http_session: MagicMock,
        mock_time: MagicMock,
        mock_logger: MagicMock,
    ):

        mock_http_session.return_value = MagicMock(spec=ClientSession)

        self.session, self.mocks = get_mocked_session()

        self.mocks["http_session"] = mock_http_session.return_value
        self.mocks["time"] = mock_time
        self.mocks["logger"] = mock_logger

        self.mocks["time"].return_value = 400

        self.mocks["http_session"].post = AsyncMock()
        self.mocks["http_session"].post.return_value = MagicMock()
        self.mocks["response"] = self.mocks["http_session"].post.return_value
        self.mocks["response"].json = AsyncMock()
        self.mocks["response"].json.side_effect = ClientError()
        self.mocks["response"].status = 400
        self.mocks["response"].raise_for_status.side_effect = ClientError()

        with self.assertRaises(ClientError):
            self.result = await self.session.async_refresh_token()

        try:
            self.mocks["logger"].error.assert_called_with(
                "Token request for %s failed with status %s (%s): %s",
                "spotcast",
                400,
                "unknown",
                "unknown_error",
            )
        except AssertionError as exc:
            self.fail(exc)


class TestServerErrorResponse(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.LOGGER", new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.time", new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def test_error_raised(
        self,
        mock_http_session: MagicMock,
        mock_time: MagicMock,
        mock_logger: MagicMock,
    ):

        mock_http_session.return_value = MagicMock(spec=ClientSession)

        self.session, self.mocks = get_mocked_session()

        self.mocks["http_session"] = mock_http_session.return_value
        self.mocks["logger"] = mock_logger

        self.mocks["http_session"].post = AsyncMock()
        self.mocks["http_session"].post.return_value = MagicMock()
        self.mocks["response"] = self.mocks["http_session"].post.return_value
        self.mocks["response"].status = 503

        with self.assertRaises(InternalServerError) as ctx:
            await self.session.async_refresh_token()

        self.assertEqual(ctx.exception.code, 503)

    @patch(f"{TEST_MODULE}.LOGGER", new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.time", new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def test_no_error_logged(
        self,
        mock_http_session: MagicMock,
        mock_time: MagicMock,
        mock_logger: MagicMock,
    ):

        mock_http_session.return_value = MagicMock(spec=ClientSession)

        self.session, self.mocks = get_mocked_session()

        self.mocks["http_session"] = mock_http_session.return_value

        self.mocks["http_session"].post = AsyncMock()
        self.mocks["http_session"].post.return_value = MagicMock()
        self.mocks["response"] = self.mocks["http_session"].post.return_value
        self.mocks["response"].status = 503

        with self.assertRaises(InternalServerError):
            await self.session.async_refresh_token()

        try:
            mock_logger.error.assert_not_called()
        except AssertionError as exc:
            self.fail(exc)
