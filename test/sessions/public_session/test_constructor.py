"""Module to test the constructor of the PublicSession class"""

from unittest import TestCase

from test.sessions.public_session import get_mocked_session


class TestDataRetention(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()

    def test_implementation_retained(self):
        self.assertIs(
            self.session.implementation,
            self.mocks["implementation"],
        )
