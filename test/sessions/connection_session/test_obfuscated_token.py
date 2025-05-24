"""Moduel to test the obfuscated_token property of the ConnectionSession class"""

from time import time
from unittest import TestCase

from test.sessions.connection_session import get_mocked_session


class TestTokenObfuscation(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()

    def test_standard_token(self):
        self.session.token["access_token"] = (
            "ABCsadfasdjngasdkhjvbashjdvbajshdvbjahsdbvajshdbvjahsbdv123"
        )

        self.assertEqual(
            self.session.obfuscated_token,
            "ABC********************123",
        )
