"""Playback control and device management for the Spotify account.

Classes:
    PlaybackMixin
"""

from asyncio import sleep, TimeoutError
from logging import getLogger
from time import time

from spotipy import SpotifyException

from custom_components.spotcast.spotify.exceptions import PlaybackError

LOGGER = getLogger(__name__)


class PlaybackMixin:
    """Devices, playback state, and playback commands for the account."""

    @property
    def devices(self) -> list:
        """Returns the list of devices linked to the account."""
        return self.get_dataset("devices")

    @property
    def playback_state(self) -> list:
        """Returns the list of devices linked to the account."""
        return self.get_dataset("playback_state")

    @property
    def active_device(self) -> str:
        """Returns the current active device."""
        playback_state = self.playback_state

        if self.playback_state == {}:
            return None

        return playback_state["device"]["id"]

    async def async_devices(self, force: bool = False) -> list[dict]:
        """Returns the list of devices."""
        await self.async_ensure_tokens_valid()
        LOGGER.debug("Getting Devices for account `%s`", self.name)

        dataset = self._datasets["devices"]

        async with dataset.lock:
            if force or dataset.is_expired():
                LOGGER.debug("Refreshing devices dataset")
                data = await self.hass.async_add_executor_job(
                    self.apis["public"].devices
                )
                dataset.update(data["devices"])
            else:
                LOGGER.debug("Using Cached devices dataset")

        return self.devices

    async def async_last_playback_state(self) -> dict:
        """The last known playback state"""

        if self._last_playback_state != {}:
            return self._last_playback_state

        return await self._playback_store.async_load() or {}

    async def async_playback_state(self, force: bool = False) -> dict:
        """Returns the current playback state"""
        await self.async_ensure_tokens_valid()
        LOGGER.debug("Getting Playback Sate for account `%s`", self.name)

        dataset = self._datasets["playback_state"]

        async with dataset.lock:
            if force or dataset.is_expired():
                LOGGER.debug("Refreshing playback state dataset")
                data = await self.hass.async_add_executor_job(
                    self.apis["public"].current_playback,
                    self.country,
                    "episode",
                )

                if data is None:
                    data = {}
                else:
                    self._last_playback_state = data
                    await self._playback_store.async_save(data)

                dataset.update(data)
            else:
                LOGGER.debug("Using Cached playback state dataset")

        return self.playback_state

    async def async_wait_for_device(self, device_id: str, timeout: int = 12):
        """Asycnhronously wait for a device to become available.

        Args:
            device_id(str): the spotify id of the device to wait for
            timeout(int): the timeout delay to wait for before
                raising an error.

        Raises:
            - TimeoutError: raised when waiting for the device goes
                beyond the set delay
        """
        LOGGER.debug("Waiting for device `%s` to become available", device_id)

        end_time = time() + timeout

        while time() <= end_time:
            devices = await self.async_devices(force=True)
            devices = {x["id"]: x for x in devices}

            try:
                devices[device_id]
                return
            except KeyError:
                LOGGER.debug("Device `%s` not yet available", device_id)
                await sleep(timeout / 4)

        raise TimeoutError(
            f"device `{device_id}` still not available after {timeout} sec."
        )

    async def async_apply_extras(
        self,
        device_id: str,
        extras: dict,
    ):
        """Applies extra settings on an account.

        Args:
            account(SpotifyAccount): the account to apply extras to
            device_id(str): the device to set the extras to
            extras(dict): the extra settings to apply
        """
        actions = {
            "volume": self.async_set_volume,
            "shuffle": self.async_shuffle,
            "repeat": self.async_repeat,
        }

        for key, value in extras.items():
            if key not in actions:
                continue

            try:
                await actions[key](value, device_id)
            except SpotifyException as exc:
                LOGGER.warning(
                    "Could not apply %s=%s to device %s: %s",
                    key,
                    value,
                    device_id,
                    exc.msg,
                )

    async def async_play_media(
        self,
        device_id: str,
        context_uri: str = None,
        uris: list[str] = None,
        offset: int | str = None,
        position: int = None,
        **_,
    ) -> None:
        """Play the media linked to the uri provided on the device requested.

        Args:
            device_id(str): The spotify device id to play media on
            context_uri(str, optional): The uri of the media to play.
                Defaults to None.
            uris(list[str], optional): List of uris to play in a
                custom context. Defaults to None.
            offset(int | str, optional): Where to start within the
                context. An int is treated as a track position; a track
                uri string starts at that track directly (avoids having
                to resolve its position).
            position(int, optional): The position in the song to start
                at the media.

        Raises:
            - PlaybackError: raised when spotipy raises an error while
                trying to start playback
        """
        await self.async_ensure_tokens_valid()

        if context_uri is None and (uris == [] or uris is None):
            LOGGER.info("transfering playback to device `%s`", device_id)
            try:
                await self.hass.async_add_executor_job(
                    self.apis["public"].transfer_playback,
                    device_id,
                    True,
                )
                return
            except SpotifyException as exc:
                raise PlaybackError(exc.msg) from exc

        LOGGER.info(
            "Starting playback of `%s` on device `%s`", context_uri, device_id
        )

        if offset is not None:
            if isinstance(offset, str):
                offset = {"uri": offset}
            else:
                offset = {"position": offset}

        if position is not None:
            position = int(position * 1000)

        if context_uri is not None and context_uri.startswith("spotify:track:"):
            uris = [context_uri]
            context_uri = None

        start_args = (
            self.apis["public"].start_playback,
            device_id,
            context_uri,
            uris,
            offset,
            position,
        )

        try:
            await self.hass.async_add_executor_job(*start_args)
        except SpotifyException as exc:
            if exc.http_status != 404:
                raise PlaybackError(exc.msg) from exc

            # A Spotify Connect device that just came online (e.g. a
            # librespot device) may not be registered yet when we issue
            # the play command, so Spotify answers 404 "Device not found".
            # Wait for it to appear and retry once before giving up,
            # instead of surfacing an error the user cannot act on.
            LOGGER.info(
                "Device `%s` not found on first play attempt; waiting for "
                "it to become available",
                device_id,
            )

            try:
                await self.async_wait_for_device(device_id)
                await self.hass.async_add_executor_job(*start_args)
            except TimeoutError as timeout_exc:
                raise PlaybackError(
                    f"Device `{device_id}` is not available on Spotify "
                    "Connect."
                ) from timeout_exc
            except SpotifyException as retry_exc:
                raise PlaybackError(retry_exc.msg) from retry_exc

    async def async_shuffle(
        self,
        shuffle: bool,
        device_id: str,
    ):
        """Sets the shuffle mode for a device.

        Args:
            shuffle(bool): Sets the shuffle mode to True or False
                based on the value provided
            device_id(str): the device to set the shuffle mode on
        """
        await self.async_ensure_tokens_valid()

        LOGGER.info(
            "Setting shuffle to %s on device `%s`", str(shuffle), device_id
        )

        await self.hass.async_add_executor_job(
            self.apis["public"].shuffle,
            shuffle,
            device_id,
        )

    async def async_repeat(
        self,
        state: str,
        device_id: str,
    ):
        """Sets the repeat mode for a device.

        Args:
            state(str): Sets the repeat mode for the device
            device_id(str): the device to set the repeat mode
        """
        await self.async_ensure_tokens_valid()

        LOGGER.info(
            "Setting repeat state to %s on device `%s`", str(state), device_id
        )

        await self.hass.async_add_executor_job(
            self.apis["public"].repeat,
            state,
            device_id,
        )

    async def async_set_volume(
        self,
        volume: int,
        device_id: str,
    ):
        """Sets the volume level for a device

        Args:
            - volume(int): The percentage of volume to set
            - device_id(str): the device to set the repeat mode
        """
        await self.async_ensure_tokens_valid()

        LOGGER.info("Setting volume to %d%% for device `%s`", volume, device_id)

        await self.hass.async_add_executor_job(
            self.apis["public"].volume,
            volume,
            device_id,
        )

    async def async_add_to_queue(self, uri: str, device_id: str = None):
        """Adds an item to the playback queue

        Args:
            - uri(str): the spotify item to add to the queue
            - device_id(str, optional): The id of the device this
                command is targeting. If None, the account's currently
                active device is the target. Defaults to None.
        """
        await self.async_ensure_tokens_valid()

        try:
            await self.hass.async_add_executor_job(
                self.apis["public"].add_to_queue,
                uri,
                device_id,
            )
        except SpotifyException as exc:
            raise PlaybackError(
                f"Could not add `{uri}` to device `{device_id}`"
            ) from exc
