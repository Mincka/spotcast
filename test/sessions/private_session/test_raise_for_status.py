"""Module to test the raise_for_status method of the PrivateSession"""

from unittest import TestCase

from custom_components.spotcast.sessions.exceptions import (
    ExpiredSpotifyCookiesError,
    InternalServerError,
    TokenRefreshError,
)

from test.sessions.private_session import get_mocked_session


class TestServerErrors(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()

    def test_500_range_raises_internal_server_error(self):
        with self.assertRaises(InternalServerError):
            self.session.raise_for_status(503, "boom", {})

    def test_status_104_raises_internal_server_error(self):
        with self.assertRaises(InternalServerError):
            self.session.raise_for_status(104, "reset", {})


class TestExpiredCookies(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()

    def test_authfailed_redirect_raises_expired_cookies(self):
        headers = {"Location": self.session.EXPIRED_LOCATION}
        with self.assertRaises(ExpiredSpotifyCookiesError):
            self.session.raise_for_status(302, "", headers)

    def test_session_marked_unhealthy(self):
        headers = {"Location": self.session.EXPIRED_LOCATION}
        try:
            self.session.raise_for_status(302, "", headers)
        except ExpiredSpotifyCookiesError:
            pass
        self.assertFalse(self.session._is_healthy)


class TestClientErrors(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()

    def test_400_range_raises_token_refresh_error(self):
        with self.assertRaises(TokenRefreshError):
            self.session.raise_for_status(403, "{}", {})

    def test_invalid_json_raises_token_refresh_error(self):
        with self.assertRaises(TokenRefreshError):
            self.session.raise_for_status(200, "<html>not json</html>", {})


class TestHealthyResponse(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()

    def test_valid_response_does_not_raise(self):
        try:
            self.session.raise_for_status(200, '{"accessToken": "foo"}', {})
        except Exception as exc:  # pylint: disable=broad-except
            self.fail(exc)
