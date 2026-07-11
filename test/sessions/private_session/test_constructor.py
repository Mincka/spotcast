"""Module to test the constructor of the PrivateSession class"""

from unittest import TestCase

from test.sessions.private_session import get_mocked_session


class TestDefaultValues(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()

    def test_access_token_starts_empty(self):
        self.assertIsNone(self.session._access_token)

    def test_expires_at_starts_at_zero(self):
        self.assertEqual(self.session._expires_at, 0)

    def test_totp_created(self):
        self.assertIsNotNone(self.session._totp)

    def test_token_property_returns_access_token(self):
        self.session._access_token = "12345"
        self.assertEqual(self.session.token, "12345")

    def test_clean_token_returns_same_as_token(self):
        self.session._access_token = "12345"
        self.assertEqual(self.session.clean_token, self.session.token)
