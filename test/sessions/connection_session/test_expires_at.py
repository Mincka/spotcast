"""Moduel to test the expires_at property of the ConnectionSession class"""

from unittest import TestCase

from test.sessions.connection_session import get_mocked_session


class TestExpirationProperty(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()

    def test_expires_at_value(self):
        self.assertEqual(self.session.expires_at, 123)
