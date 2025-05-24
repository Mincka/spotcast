"""Moduel to test the valid_token property of the ConnectionSession class"""

from time import time
from unittest import TestCase

from test.sessions.connection_session import get_mocked_session


class TestTokenIsValid(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()
        self.session.data["token"]["expires_at"] = time() + 9999

    def test_is_valid(self):
        self.assertTrue(self.session.valid_token)


class TestTokenIsNotValid(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()
        self.session.data["token"]["expires_at"] = time() - 9999

    def test_is_valid(self):
        self.assertFalse(self.session.valid_token)
