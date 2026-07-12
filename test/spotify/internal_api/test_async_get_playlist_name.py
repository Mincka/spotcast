"""Module to test the async_get_playlist_name function"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from custom_components.spotcast.spotify.internal_api import (
    async_get_playlist_name,
    SPCLIENT_BASE,
)

from test.spotify.internal_api import TEST_MODULE


def _account_with_response(response: MagicMock):
    account = MagicMock()
    account.async_get_token = AsyncMock(return_value="desktop-token")
    session = MagicMock()
    session.get = AsyncMock(return_value=response)
    return account, session


class TestNameResolved(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def asyncSetUp(self, mock_session: MagicMock):

        response = MagicMock()
        response.status = 200
        response.json = AsyncMock(
            return_value={
                "length": 50,
                "attributes": {
                    "name": "Today's Top Hits",
                    "description": "The hottest 50.",
                },
            }
        )

        self.account, self.session = _account_with_response(response)
        mock_session.return_value = self.session

        self.result = await async_get_playlist_name(
            self.account,
            "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",
        )

    def test_name_returned(self):
        self.assertEqual(self.result, "Today's Top Hits")

    def test_metadata_endpoint_called(self):
        expected = (
            f"{SPCLIENT_BASE}/playlist/v2/playlist/"
            "37i9dQZF1DXcBWIGoYBM5M/metadata"
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


class TestMissingName(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def test_no_attributes_returns_none(self, mock_session: MagicMock):

        response = MagicMock()
        response.status = 200
        response.json = AsyncMock(return_value={"length": 50})

        account, session = _account_with_response(response)
        mock_session.return_value = session

        result = await async_get_playlist_name(
            account, "spotify:playlist:foo"
        )

        self.assertIsNone(result)

    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def test_empty_name_returns_none(self, mock_session: MagicMock):

        response = MagicMock()
        response.status = 200
        response.json = AsyncMock(return_value={"attributes": {"name": ""}})

        account, session = _account_with_response(response)
        mock_session.return_value = session

        result = await async_get_playlist_name(
            account, "spotify:playlist:foo"
        )

        self.assertIsNone(result)

    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def test_name_not_str_returns_none(self, mock_session: MagicMock):

        response = MagicMock()
        response.status = 200
        response.json = AsyncMock(
            return_value={"attributes": {"name": 1234}}
        )

        account, session = _account_with_response(response)
        mock_session.return_value = session

        result = await async_get_playlist_name(
            account, "spotify:playlist:foo"
        )

        self.assertIsNone(result)


class TestUnavailable(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def test_non_ok_status_returns_none(self, mock_session: MagicMock):

        response = MagicMock()
        response.status = 404
        response.json = AsyncMock(return_value={"attributes": {"name": "x"}})

        account, session = _account_with_response(response)
        mock_session.return_value = session

        result = await async_get_playlist_name(
            account, "spotify:playlist:foo"
        )

        self.assertIsNone(result)
        response.json.assert_not_called()

    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def test_token_unavailable_returns_none(
        self, mock_session: MagicMock
    ):

        account = MagicMock()
        account.async_get_token = AsyncMock(side_effect=RuntimeError("boom"))

        result = await async_get_playlist_name(
            account, "spotify:playlist:foo"
        )

        self.assertIsNone(result)
        mock_session.assert_not_called()
