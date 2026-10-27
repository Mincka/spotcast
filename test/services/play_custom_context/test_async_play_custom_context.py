"""Module to test the async_play_custom_context function"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from custom_components.spotcast.services.play_custom_context import (
    async_play_custom_context,
    HomeAssistant,
    ServiceCall,
    SpotifyAccount,
    MissingActiveDeviceError,
    AccountMismatchError,
    ServiceValidationError,
)
from custom_components.spotcast.media_player._abstract_player import (
    MediaPlayer
)

TEST_MODULE = "custom_components.spotcast.services.play_custom_context"
SERVICE = async_play_custom_context
CALL_DATA = {
    "media_player": {"entity_id": ["media_player.foo"]},
    "tracks": ["foo", "bar"],
}


class TestPlayContext(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_media_player_from_id")
    @patch(f"{TEST_MODULE}.get_account_entry", new_callable=MagicMock)
    @patch.object(SpotifyAccount, "async_from_config_entry")
    async def asyncSetUp(
            self,
            mock_account: AsyncMock,
            mock_entry: MagicMock,
            mock_media_player: AsyncMock,
    ):

        mock_account.return_value = MagicMock(spec=SpotifyAccount)
        mock_media_player.return_value = MagicMock(spec=MediaPlayer)

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "call": MagicMock(spec=ServiceCall),
            "account": mock_account.return_value,
            "media_player": mock_media_player.return_value,
        }

        self.mocks["call"].data = {
            "media_player": {
                "entity_id": [
                    "media_player.foo"
                ]
            },
            "tracks": ["foo", "bar"]
        }

        self.mocks["hass"].data = {}
        self.mocks["media_player"].id = "12345"

        await async_play_custom_context(
            self.mocks["hass"],
            self.mocks["call"],
        )

    def test_async_play_media_called_properly(self):
        try:
            self.mocks["account"].async_play_media.assert_called_with(
                "12345",
                uris=["foo", "bar"],
            )
        except AssertionError:
            self.fail()

    def test_apply_extras_called_properly(self):
        try:
            self.mocks["account"].async_apply_extras(
                "12345",
                None
            )
        except AssertionError:
            self.fail()


class TestPlayContextWithExtras(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.randint", new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.async_media_player_from_id")
    @patch(f"{TEST_MODULE}.get_account_entry", new_callable=MagicMock)
    @patch.object(SpotifyAccount, "async_from_config_entry")
    async def asyncSetUp(
            self,
            mock_account: AsyncMock,
            mock_entry: MagicMock,
            mock_media_player: AsyncMock,
            mock_random: MagicMock,
    ):

        mock_account.return_value = MagicMock(spec=SpotifyAccount)
        mock_media_player.return_value = MagicMock(spec=MediaPlayer)
        mock_random.return_value = 1

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "call": MagicMock(spec=ServiceCall),
            "account": mock_account.return_value,
            "media_player": mock_media_player.return_value,
        }

        self.mocks["call"].data = {
            "media_player": {
                "entity_id": [
                    "media_player.foo"
                ]
            },
            "tracks": ["foo", "bar"],
            "data": {
                "volume": 80,
                "position_ms": 5000,
                "random": True,
            }
        }

        self.mocks["hass"].data = {}
        self.mocks["media_player"].id = "12345"

        await async_play_custom_context(
            self.mocks["hass"],
            self.mocks["call"],
        )

    def test_async_play_media_called_properly(self):
        try:
            self.mocks["account"].async_play_media.assert_called_with(
                "12345",
                uris=["foo", "bar"],
                position_ms=5000,
                volume=80,
                random=True,
                offset=1,
            )
        except AssertionError:
            self.fail()

    def test_apply_extras_called_properly(self):
        try:
            self.mocks["account"].async_apply_extras(
                "12345",
                {
                    "volume": 80,
                    "position_ms": 5000,
                    "random": True,
                    "offset": 1,
                }
            )
        except AssertionError:
            self.fail()


class TestPlayContextFromActiveDevice(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_media_player_from_id")
    @patch(f"{TEST_MODULE}.get_account_entry", new_callable=MagicMock)
    @patch.object(SpotifyAccount, "async_from_config_entry")
    async def asyncSetUp(
            self,
            mock_account: AsyncMock,
            mock_entry: MagicMock,
            mock_media_player: AsyncMock,
    ):

        mock_account.return_value = MagicMock(spec=SpotifyAccount)
        mock_media_player.return_value = MagicMock(spec=MediaPlayer)

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "call": MagicMock(spec=ServiceCall),
            "account": mock_account.return_value,
            "media_player": mock_media_player.return_value,
        }

        self.mocks["call"].data = {
            "tracks": ["foo", "bar"]
        }

        self.mocks["hass"].data = {}
        self.mocks["media_player"].id = "12345"

        await async_play_custom_context(
            self.mocks["hass"],
            self.mocks["call"],
        )

    def test_async_play_media_called_properly(self):
        try:
            self.mocks["account"].async_play_media.assert_called_with(
                "12345",
                uris=["foo", "bar"],
            )
        except AssertionError:
            self.fail()

    def test_apply_extras_called_properly(self):
        try:
            self.mocks["account"].async_apply_extras(
                "12345",
                None
            )
        except AssertionError:
            self.fail()


class TestMissingActiveDevice(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_media_player_from_id")
    @patch(f"{TEST_MODULE}.get_account_entry", new_callable=MagicMock)
    @patch.object(SpotifyAccount, "async_from_config_entry")
    async def test_error_raised(
            self,
            mock_account: AsyncMock,
            mock_entry: MagicMock,
            mock_media_player: AsyncMock,
    ):

        mock_account.return_value = MagicMock(spec=SpotifyAccount)
        mock_media_player.side_effect = MissingActiveDeviceError()

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "call": MagicMock(spec=ServiceCall),
            "account": mock_account.return_value,
            "media_player": mock_media_player.return_value,
        }

        self.mocks["call"].data = {
            "tracks": ["foo", "bar"]
        }

        self.mocks["hass"].data = {}
        self.mocks["media_player"].id = "12345"

        with self.assertRaises(ServiceValidationError):
            await async_play_custom_context(
                self.mocks["hass"],
                self.mocks["call"],
            )


class TestEntityOfOtherAccount(IsolatedAsyncioTestCase):
    """A `*_spotcast` entity of another account is a user error, so it
    surfaces as a ServiceValidationError (see #76)."""

    @patch(f"{TEST_MODULE}.async_media_player_from_id")
    @patch(f"{TEST_MODULE}.get_account_entry", new_callable=MagicMock)
    @patch.object(SpotifyAccount, "async_from_config_entry")
    async def test_error_raised(
            self,
            mock_account: AsyncMock,
            mock_entry: MagicMock,
            mock_media_player: AsyncMock,
    ):

        mock_account.return_value = MagicMock(spec=SpotifyAccount)
        mock_media_player.side_effect = AccountMismatchError("other")

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "call": MagicMock(spec=ServiceCall),
        }

        self.mocks["call"].data = {
            "media_player": {
                "entity_id": [
                    "media_player.foo_other_spotcast"
                ]
            },
            "tracks": ["foo", "bar"]
        }

        self.mocks["hass"].data = {}

        with self.assertRaises(ServiceValidationError):
            await async_play_custom_context(
                self.mocks["hass"],
                self.mocks["call"],
            )


class TestMediaPlayerReleased(IsolatedAsyncioTestCase):
    """The media player is released once playback is handed to Spotify,
    and also when starting it fails (see #80)."""

    async def _play(self, play_side_effect=None):
        with (
            patch(f"{TEST_MODULE}.async_media_player_from_id") as mock_player,
            patch(f"{TEST_MODULE}.get_account_entry", new_callable=MagicMock),
            patch.object(
                SpotifyAccount,
                "async_from_config_entry",
            ) as mock_account,
        ):
            mock_account.return_value = MagicMock(spec=SpotifyAccount)
            mock_account.return_value.async_play_media.side_effect = (
                play_side_effect
            )
            mock_player.return_value = MagicMock(spec=MediaPlayer)
            mock_player.return_value.id = "12345"
            self.order = []
            mock_account.return_value.async_apply_extras.side_effect = (
                lambda *_: self.order.append("extras")
            )
            mock_player.return_value.release.side_effect = (
                lambda: self.order.append("release")
            )
            self.mock_account = mock_account.return_value
            self.mock_player = mock_player.return_value

            hass = MagicMock(spec=HomeAssistant)
            hass.data = {}
            call = MagicMock(spec=ServiceCall)
            call.data = CALL_DATA

            await SERVICE(hass, call)

    async def test_released_after_playback(self):
        await self._play()

        self.mock_player.release.assert_called_once_with()

    async def test_released_after_extras_applied(self):
        await self._play()

        self.assertEqual(self.order, ["extras", "release"])

    async def test_released_when_playback_fails(self):
        with self.assertRaises(RuntimeError):
            await self._play(RuntimeError("Spotify refused"))

        self.mock_player.release.assert_called_once_with()
