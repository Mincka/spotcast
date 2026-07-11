"""Module to test the cookies property of the PrivateSession"""

from unittest import TestCase

from test.sessions.private_session import get_mocked_session


class TestCookieContent(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()

    def test_cookies_built_from_entry_data(self):
        self.assertEqual(
            self.session.cookies,
            {"sp_dc": "foo", "sp_key": "bar"},
        )
