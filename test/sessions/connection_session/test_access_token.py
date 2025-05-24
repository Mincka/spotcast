"""Moduel to test the access_token property of the ConnectionSession class"""

from unittest import TestCase

from test.sessions.connection_session import get_mocked_session


class TestAccessTokenGetter(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()

    def test_data_value(self):
        self.assertEqual(self.session.access_token, "foo")
