"""Module to test the async_get_playlist_length function"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from aiohttp import ClientError

from custom_components.spotcast.spotify.internal_api import (
    async_get_playlist_length,
    SPCLIENT_BASE,
)

from test.spotify.internal_api import TEST_MODULE


def _account_with_response(response: MagicMock) -> MagicMock:
    """Builds a mocked account whose desktop token resolves and whose
    client session returns the provided response."""
    account = MagicMock()
    account.async_get_token = AsyncMock(return_value="desktop-token")
    session = MagicMock()
    session.get = AsyncMock(return_value=response)
    account._session = session
    return account, session


class TestLengthResolved(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def asyncSetUp(self, mock_session: MagicMock):

        response = MagicMock()
        response.status = 200
        response.json = AsyncMock(return_value={"length": 50})

        self.account, self.session = _account_with_response(response)
        mock_session.return_value = self.session
        self.mock_session = mock_session

        self.result = await async_get_playlist_length(
            self.account,
            "spotify:playlist:37i9dQZF1DX4sWSpwq3LiO",
        )

    def test_length_returned(self):
        self.assertEqual(self.result, 50)

    def test_metadata_endpoint_called(self):
        expected = (
            f"{SPCLIENT_BASE}/playlist/v2/playlist/"
            "37i9dQZF1DX4sWSpwq3LiO/metadata"
        )
        try:
            self.session.get.assert_called_once_with(
                expected,
                headers={
                    "authorization": "Bearer desktop-token",
                    "accept": "application/json",
                },
            )
        except AssertionError as exc:
            self.fail(exc)


class TestBareIdAccepted(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def test_bare_id_used_in_url(self, mock_session: MagicMock):

        response = MagicMock()
        response.status = 200
        response.json = AsyncMock(return_value={"length": 12})

        account, session = _account_with_response(response)
        mock_session.return_value = session

        result = await async_get_playlist_length(account, "abc123")

        self.assertEqual(result, 12)
        session.get.assert_called_once_with(
            f"{SPCLIENT_BASE}/playlist/v2/playlist/abc123/metadata",
            headers={
                "authorization": "Bearer desktop-token",
                "accept": "application/json",
            },
        )


class TestTokenUnavailable(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def test_returns_none(self, mock_session: MagicMock):

        account = MagicMock()
        account.async_get_token = AsyncMock(side_effect=RuntimeError("boom"))

        result = await async_get_playlist_length(
            account, "spotify:playlist:foo"
        )

        self.assertIsNone(result)
        mock_session.assert_not_called()


class TestRequestError(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def test_returns_none(self, mock_session: MagicMock):

        account = MagicMock()
        account.async_get_token = AsyncMock(return_value="desktop-token")
        session = MagicMock()
        session.get = AsyncMock(side_effect=ClientError("network"))
        mock_session.return_value = session

        result = await async_get_playlist_length(
            account, "spotify:playlist:foo"
        )

        self.assertIsNone(result)


class TestNonOkStatus(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def test_returns_none(self, mock_session: MagicMock):

        response = MagicMock()
        response.status = 404
        response.json = AsyncMock(return_value={"length": 50})

        account, session = _account_with_response(response)
        mock_session.return_value = session

        result = await async_get_playlist_length(
            account, "spotify:playlist:foo"
        )

        self.assertIsNone(result)
        response.json.assert_not_called()


class TestInvalidJson(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def test_returns_none(self, mock_session: MagicMock):

        response = MagicMock()
        response.status = 200
        response.json = AsyncMock(side_effect=ValueError("not json"))

        account, session = _account_with_response(response)
        mock_session.return_value = session

        result = await async_get_playlist_length(
            account, "spotify:playlist:foo"
        )

        self.assertIsNone(result)


class TestMissingLength(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def test_returns_none_when_length_absent(
        self, mock_session: MagicMock
    ):

        response = MagicMock()
        response.status = 200
        response.json = AsyncMock(return_value={"attributes": {}})

        account, session = _account_with_response(response)
        mock_session.return_value = session

        result = await async_get_playlist_length(
            account, "spotify:playlist:foo"
        )

        self.assertIsNone(result)

    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def test_returns_none_when_length_not_int(
        self, mock_session: MagicMock
    ):

        response = MagicMock()
        response.status = 200
        response.json = AsyncMock(return_value={"length": "many"})

        account, session = _account_with_response(response)
        mock_session.return_value = session

        result = await async_get_playlist_length(
            account, "spotify:playlist:foo"
        )

        self.assertIsNone(result)
