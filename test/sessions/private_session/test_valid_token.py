"""Module to test the valid_token property of the PrivateSession"""

from time import time
from unittest import TestCase

from test.sessions.private_session import get_mocked_session


class TestExpiredToken(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()

    def test_new_session_token_is_invalid(self):
        self.assertFalse(self.session.valid_token)

    def test_past_expiration_is_invalid(self):
        self.session._expires_at = time() - 10
        self.assertFalse(self.session.valid_token)

    def test_future_expiration_is_valid(self):
        self.session._expires_at = time() + 3600
        self.assertTrue(self.session.valid_token)
