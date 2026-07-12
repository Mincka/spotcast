"""Module to test async_rebuild_playback"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from custom_components.spotcast.services.transfer_playback import (
    async_rebuild_playback,
    SpotifyAccount,
)

from test.services.transfer_playback import TEST_MODULE


class TestRepeatOveride(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount),
        }

        self.mocks["account"].async_last_playback_state = AsyncMock()
        self.mocks["account"].async_last_playback_state.return_value = {
            "repeat_state": "context",
            "shuffle_state": True,
            "context": {
                "uri": "spotify:album:foo",
                "type": "album"
            },
        }

        self.call_data = {
            "media_player": {
                "entity_id": [
                    "media_player.foo"
                ]
            },
            "data": {
                "offset": 2,
                "position": 5
            }
        }

    async def test_repeat_is_not_set(self):
        self.call_data["data"]["repeat"] = "off"
        result = await async_rebuild_playback(
            self.call_data,
            self.mocks["account"],
        )

        self.assertEqual(result["data"]["repeat"], "off")

    async def test_repeat_was_set(self):
        result = await async_rebuild_playback(
            self.call_data,
            self.mocks["account"],
        )

        self.assertEqual(result["data"]["repeat"], "context")


class TestShuffleOveride(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount),
        }

        self.mocks["account"]._last_playback_state = {
            "repeat_state": "context",
            "shuffle_state": True,
            "context": {
                "uri": "spotify:album:foo",
                "type": "album"
            },
        }

        self.call_data = {
            "media_player": {
                "entity_id": [
                    "media_player.foo"
                ]
            },
            "data": {
                "offset": 2,
                "position": 5,
            }
        }

    async def test_repeat_is_not_set(self):
        self.call_data["data"]["shuffle"] = False
        result = await async_rebuild_playback(
            self.call_data,
            self.mocks["account"],
        )

        self.assertFalse(result["data"]["shuffle"])

    async def test_repeat_was_set(self):
        result = await async_rebuild_playback(
            self.call_data,
            self.mocks["account"],
        )

        self.assertTrue(result["data"]["shuffle"])


class TestCurrentItemIsPartOfAlbumContext(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_track_index")
    async def asyncSetUp(self, mock_index: AsyncMock):

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount),
            "index": mock_index,
        }

        self.mocks["account"].async_last_playback_state = AsyncMock()
        self.mocks["account"].async_last_playback_state.return_value = {
            "repeat_state": "context",
            "shuffle_state": True,
            "context": {
                "uri": "spotify:album:foo",
                "type": "album"
            },
            "item": {
                "album": {
                    "uri": "spotify:album:foo"
                },
                "uri": "spotify:track:bar"
            }
        }

        self.mocks["index"].return_value = ("dummy_uri", 5)

        self.call_data = {
            "media_player": {
                "entity_id": [
                    "media_player.foo"
                ]
            },
            "data": {
                "position": 5
            }
        }

        self.result = await async_rebuild_playback(
            self.call_data,
            self.mocks["account"],
        )

    def test_returned_expected_call_data(self):
        self.assertEqual(
            self.result,
            {
                "media_player": {
                    "entity_id": [
                        "media_player.foo"
                    ]
                },
                "spotify_uri": "spotify:album:foo",
                "data": {
                    "offset": 4,
                    "shuffle": True,
                    "repeat": "context",
                    "position": 5
                }
            }
        )


class TestCurrentItemNotPartOfAlbumContext(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_track_index")
    async def asyncSetUp(self, mock_index: AsyncMock):

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount),
            "index": mock_index,
        }

        self.mocks["account"].async_last_playback_state = AsyncMock()
        self.mocks["account"].async_last_playback_state.return_value = {
            "repeat_state": "context",
            "shuffle_state": True,
            "context": {
                "uri": "spotify:album:foo",
                "type": "album"
            },
            "item": {
                "album": {
                    "uri": "spotify:album:baz"
                },
                "uri": "spotify:track:bar"
            }
        }

        self.mocks["index"].side_effect = ValueError()

        self.call_data = {
            "media_player": {
                "entity_id": [
                    "media_player.foo"
                ]
            },
            "data": {
                "position": 5
            }
        }

        self.result = await async_rebuild_playback(
            self.call_data,
            self.mocks["account"],
        )

    def test_returned_expected_call_data(self):
        self.assertEqual(
            self.result,
            {
                "media_player": {
                    "entity_id": [
                        "media_player.foo"
                    ]
                },
                "spotify_uri": "spotify:album:foo",
                "data": {
                    "offset": 0,
                    "shuffle": True,
                    "repeat": "context",
                    "position": 5
                }
            }
        )


class TestPlaylistContext(IsolatedAsyncioTestCase):
    """A playlist context resumes directly at the current track's uri,
    without paginating the whole playlist to find its numeric index. This
    is what fixes the slow transfer on large playlists (see #582)."""

    @patch(f"{TEST_MODULE}.async_track_index")
    async def asyncSetUp(self, mock_index: AsyncMock):

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount),
            "index": mock_index,
        }

        self.mocks["account"].async_last_playback_state = AsyncMock()
        self.mocks["account"].async_last_playback_state.return_value = {
            "repeat_state": "context",
            "shuffle_state": True,
            "context": {
                "uri": "spotify:playlist:foo",
                "type": "playlist"
            },
            "item": {
                "album": {
                    "uri": "spotify:album:baz"
                },
                "uri": "spotify:track:bar"
            }
        }

        self.mocks["account"].async_get_playlist_tracks = AsyncMock()

        self.call_data = {
            "media_player": {
                "entity_id": [
                    "media_player.foo"
                ]
            },
            "data": {
                "position": 5
            }
        }

        self.result = await async_rebuild_playback(
            self.call_data,
            self.mocks["account"],
        )

    def test_returned_expected_call_data(self):
        self.assertEqual(
            self.result,
            {
                "media_player": {
                    "entity_id": [
                        "media_player.foo"
                    ]
                },
                "spotify_uri": "spotify:playlist:foo",
                "data": {
                    "offset": "spotify:track:bar",
                    "shuffle": True,
                    "repeat": "context",
                    "position": 5
                }
            }
        )

    def test_track_index_not_called(self):
        try:
            self.mocks["index"].assert_not_called()
        except AssertionError:
            self.fail()

    def test_playlist_not_fetched(self):
        try:
            self.mocks["account"].async_get_playlist_tracks\
                .assert_not_called()
        except AssertionError:
            self.fail()


class TestEditorialPlaylistContext(IsolatedAsyncioTestCase):
    """Editorial/algorithmic playlists (37i9) 404 on the Web API, so the
    old index-based rebuild had to degrade. Resuming at the track uri needs
    no playlist read, so it works for editorial playlists too (#570, #582)."""

    @patch(f"{TEST_MODULE}.async_track_index")
    async def asyncSetUp(self, mock_index: AsyncMock):

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount),
            "index": mock_index,
        }

        self.mocks["account"].async_last_playback_state = AsyncMock()
        self.mocks["account"].async_last_playback_state.return_value = {
            "repeat_state": "context",
            "shuffle_state": True,
            "context": {
                "uri": "spotify:playlist:37i9dQZF1DX4sWSpwq3LiO",
                "type": "playlist"
            },
            "item": {
                "album": {
                    "uri": "spotify:album:baz"
                },
                "uri": "spotify:track:bar"
            }
        }

        self.mocks["account"].async_get_playlist_tracks = AsyncMock()

        self.call_data = {
            "media_player": {
                "entity_id": [
                    "media_player.foo"
                ]
            },
            "data": {
                "position": 5
            }
        }

        self.result = await async_rebuild_playback(
            self.call_data,
            self.mocks["account"],
        )

    def test_offset_is_track_uri(self):
        self.assertEqual(
            self.result["data"]["offset"],
            "spotify:track:bar",
        )

    def test_playlist_uri_kept(self):
        self.assertEqual(
            self.result["spotify_uri"],
            "spotify:playlist:37i9dQZF1DX4sWSpwq3LiO",
        )

    def test_playlist_not_fetched(self):
        try:
            self.mocks["account"].async_get_playlist_tracks\
                .assert_not_called()
        except AssertionError:
            self.fail()


class TestCollectionContext(IsolatedAsyncioTestCase):
    """The liked-songs (collection) context resumes at the current track's
    uri, without fetching the whole liked-songs library."""

    @patch(f"{TEST_MODULE}.async_track_index")
    async def asyncSetUp(self, mock_index: AsyncMock):

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount),
            "index": mock_index,
        }

        self.mocks["account"].async_last_playback_state = AsyncMock()
        self.mocks["account"].async_last_playback_state.return_value = {
            "repeat_state": "context",
            "shuffle_state": True,
            "progress_ms": 31415,
            "context": {
                "uri": "spotify:user:dummy:collection",
                "type": "collection"
            },
            "item": {
                "album": {
                    "uri": "spotify:album:baz"
                },
                "uri": "spotify:track:bar"
            }
        }

        self.mocks["account"].async_liked_songs = AsyncMock()

        self.call_data = {
            "media_player": {
                "entity_id": [
                    "media_player.foo"
                ]
            },
            "data": {}
        }

        self.result = await async_rebuild_playback(
            self.call_data,
            self.mocks["account"],
        )

    def test_returned_expected_call_data(self):
        self.assertEqual(
            self.result,
            {
                "media_player": {
                    "entity_id": [
                        "media_player.foo"
                    ]
                },
                "spotify_uri": "spotify:user:dummy:collection",
                "data": {
                    "offset": "spotify:track:bar",
                    "shuffle": True,
                    "repeat": "context",
                    "position": 31.415
                }
            }
        )

    def test_track_index_not_called(self):
        try:
            self.mocks["index"].assert_not_called()
        except AssertionError:
            self.fail()

    def test_liked_songs_not_fetched(self):
        try:
            self.mocks["account"].async_liked_songs.assert_not_called()
        except AssertionError:
            self.fail()


class TestUnknownContentType(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_track_index")
    async def asyncSetUp(self, mock_index: AsyncMock):

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount),
            "index": mock_index,
        }

        self.mocks["account"].async_last_playback_state = AsyncMock()
        self.mocks["account"].async_last_playback_state.return_value = {
            "repeat_state": "context",
            "shuffle_state": True,
            "context": {
                "uri": "spotify:user:dummy:collection",
                "type": "dummy"
            },
            "item": {
                "album": {
                    "uri": "spotify:album:baz"
                },
                "uri": "spotify:track:bar"
            }
        }

        self.call_data = {
            "media_player": {
                "entity_id": [
                    "media_player.foo"
                ]
            },
            "data": {
                "position": 5
            }
        }

        self.result = await async_rebuild_playback(
            self.call_data,
            self.mocks["account"],
        )

    def test_returned_expected_call_data(self):
        self.assertEqual(
            self.result,
            {
                "media_player": {
                    "entity_id": [
                        "media_player.foo"
                    ]
                },
                "spotify_uri": "spotify:user:dummy:collection",
                "data": {
                    "offset": 0,
                    "shuffle": True,
                    "repeat": "context",
                    "position": 5
                }
            }
        )

    def test_track_index_not_called(self):
        try:
            self.mocks["index"].assert_not_called()
        except AssertionError:
            self.fail()


class TestShowContext(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount)
        }

        self.mocks["account"].async_last_playback_state = AsyncMock()
        self.mocks["account"].async_last_playback_state.return_value = {
            "context": {
                "uri": "spotify:show:foo",
                "type": "show"
            },
            "item": {
                "uri": "spotify:episode:bar"
            },
            "repeat_state": "context",
            "shuffle_state": False,
            "progress_ms": 2000,
        }

        self.result = await async_rebuild_playback({}, self.mocks["account"])

    def test_context_changed_to_episode(self):
        self.assertEqual(self.result["spotify_uri"], "spotify:episode:bar")


class TestArtistContext(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self.mocks = {
            "account": MagicMock(spec=SpotifyAccount)
        }

        self.mocks["account"].async_last_playback_state = AsyncMock()
        self.mocks["account"].async_last_playback_state.return_value = {
            "context": {
                "uri": "spotify:artist:foo",
                "type": "artist"
            },
            "item": {
                "uri": "spotify:song:bar"
            },
            "repeat_state": "context",
            "shuffle_state": False,
            "progress_ms": 2000,
        }

        self.result = await async_rebuild_playback(
            {"data": {}},
            self.mocks["account"]
        )

    def test_context_unchanged(self):
        self.assertEqual(self.result["spotify_uri"], "spotify:artist:foo")

    def test_offset_removed(self):
        self.assertIsNone(self.result["data"]["offset"])
