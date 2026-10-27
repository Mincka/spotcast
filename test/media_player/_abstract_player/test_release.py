"""Module to test the default release method of the MediaPlayer"""

from unittest import TestCase

from custom_components.spotcast.media_player._abstract_player import (
    MediaPlayer,
)


class DummyPlayer(MediaPlayer):

    id = "12345"
    name = "foo"


class TestDefaultRelease(TestCase):

    def test_release_is_a_noop(self):
        self.assertIsNone(DummyPlayer().release())
