"""Module to test the headers property of the PrivateSession"""

from unittest import TestCase

from test.sessions.private_session import get_mocked_session


class TestHeaderContent(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()
        self.headers = self.session.headers

    def test_accept_header_is_json(self):
        self.assertEqual(self.headers["Accept"], "application/json")

    def test_user_agent_looks_like_a_browser(self):
        self.assertTrue(self.headers["user-agent"].startswith("Mozilla/5.0"))


class TestEndpointBuilder(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()

    def test_endpoint_prefixed_with_base_url(self):
        self.assertEqual(
            self.session._endpoint("server-time"),
            "https://open.spotify.com/server-time",
        )
