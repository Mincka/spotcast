"""Content and library reads for the Spotify account.

Classes:
    LibraryMixin
"""

from logging import getLogger

from custom_components.spotcast.spotify.search_query import SearchQuery

LOGGER = getLogger(__name__)


class LibraryMixin:
    """Playlist, track, album, episode, search, and liked-song reads."""

    @property
    def playlists(self) -> list:
        """Returns the list of playlists for the account."""
        return self.get_dataset("playlists")

    @property
    def categories(self) -> list:
        """Returns the list of Browse categories for the account."""
        return self.get_dataset("categories")

    @property
    def liked_songs(self) -> list:
        """Returns the list of liked songs for the account."""
        liked_songs = self.get_dataset("liked_songs")
        liked_songs = [x["track"]["uri"] for x in liked_songs]
        return liked_songs

    async def async_saved_episodes(
        self,
        limit: int = None,
    ) -> list[dict]:
        """Retrieves the list of podcast episode saved.

        Args:
            limit(int, optional): If not None, stops getting episode
                once the limit of item reached. Defaults to None

        Return:
            - list[dict]: a list of dictionary with the episodes
                information
        """
        await self.async_ensure_tokens_valid()
        LOGGER.debug(
            "Getting List of saved podcast episode for account `%s`",
            self.name,
        )

        return await self._async_pager(
            self.apis["public"].current_user_saved_episodes,
            appends=[self.country],
            max_items=limit,
        )

    async def async_get_track(self, uri: str) -> dict:
        """Retrieves track information.

        Args:
            uri(str): The URI of the track to search

        Returns:
            dict: the songs details
        """
        await self.async_ensure_tokens_valid()

        LOGGER.debug("Getting track information for `%s`", uri)

        result = await self.hass.async_add_executor_job(
            self.apis["public"].track, uri, self.country
        )

        return result

    async def async_get_playlist(self, uri: str) -> dict:
        """Retrieves a playlist information.

        Args:
            uri(str): the URI of the playlist to search

        Returns:
            dict: the playlist details
        """
        await self.async_ensure_tokens_valid()
        LOGGER.debug("Fetching information from playlist `%s`", uri)

        playlist_id = self._id_from_uri(uri)

        result = await self.hass.async_add_executor_job(
            self.apis["public"].playlist,
            playlist_id,
            None,
            self.country,
        )

        return result

    async def async_get_album(self, uri: str) -> dict:
        """Retrieves an album information.

        Args:
            uri(str): the URI of the album to search

        Returns:
            dict: the album details
        """
        await self.async_ensure_tokens_valid()
        LOGGER.debug("Fetching information for album `%s`", uri)

        album_id = self._id_from_uri(uri)

        result = await self.hass.async_add_executor_job(
            self.apis["public"].album,
            album_id,
            self.country,
        )

        return result

    async def async_get_artist_top_tracks(self, uri: str) -> list[dict]:
        """Retrieves the list of top tracks for an artist.

        Args:
            uri(str): the URI of the artist to search

        Returns:
            list[dict]: the list of top songes for an artist
        """
        await self.async_ensure_tokens_valid()
        LOGGER.debug("Fetching Top Tracks for artist `%s`", uri)

        result = await self.hass.async_add_executor_job(
            self.apis["public"].artist_top_tracks,
            uri,
            self.country,
        )

        return result["tracks"]

    async def async_get_playlist_tracks(self, uri: str) -> list[dict]:
        """Retrieves the list of tracks inside a playlist."""
        await self.async_ensure_tokens_valid()
        LOGGER.debug("Fetching tracks from playlist `%s`", uri)

        playlist_id = self._id_from_uri(uri)

        result = await self._async_pager(
            function=self.apis["public"].playlist_tracks,
            prepends=[playlist_id, None],
            appends=[self.country],
        )

        return result

    async def async_get_show_episodes(
        self, uri: str, limit: int = None
    ) -> list[dict]:
        """Retrieves the list of episodes for a podcast show.

        Args:
            - uri(str): the uri of the spotify podcast show to call
            - limit(int, optional): limit the number of items to
                retrieve. Retrives all episodes if None. Defaults to
                None.

        Returns:
            - list[dict]: list of dictionaries with podcast episodes
                information
        """
        await self.async_ensure_tokens_valid()
        LOGGER.debug("Fetching episodes from show `%s`", uri)

        result = await self._async_pager(
            function=self.apis["public"].show_episodes,
            prepends=[uri],
            appends=[self.country],
            max_items=limit,
        )

        return result

    async def async_get_episode(self, uri: str) -> str:
        """Retrieves the information of a podcast episode"""
        await self.async_ensure_tokens_valid()
        LOGGER.debug("Fetching information from episode `%s`", uri)

        result = await self.hass.async_add_executor_job(
            self.apis["public"].episode,
            uri,
            self.country,
        )

        return result

    async def async_playlists_count(self) -> int:
        """Returns the number of user playlist for an account."""
        await self.async_ensure_tokens_valid()

        dataset = self._datasets["playlists_count"]

        async with dataset.lock:
            if dataset.is_expired():
                LOGGER.debug("Refreshing playlists count dataset")

                count = await self._async_get_count(
                    self.apis["public"].current_user_playlists
                )

                dataset.update({"total": count})
            else:
                LOGGER.debug("Using cached playlists count dataset")

        return self.get_dataset("playlists_count")["total"]

    async def async_playlists(
        self,
        force: bool = False,
        max_items: int = None,
    ) -> list[dict]:
        """Returns a list of playlist for the current user."""
        await self.async_ensure_tokens_valid()
        LOGGER.debug("Getting Playlist for account `%s`", self.name)

        dataset = self._datasets["playlists"]

        async with dataset.lock:
            if force or dataset.is_expired():
                LOGGER.debug("Refreshing playlists dataset")

                playlists = await self._async_pager(
                    self.apis["public"].current_user_playlists,
                    max_items=max_items,
                )

                dataset.update(playlists)

            else:
                LOGGER.debug("Using cached playlists dataset")

        return self.playlists

    async def async_search(
        self,
        query: SearchQuery,
        limit: int = 20,
    ) -> list[dict]:
        """Makes a search query and returns the result.

        Args:
            query(SearchQuery): The search query to run
            limit(int, optional): The maximum amount of item to
                retrieve in each category. Defaults to 20.
        """
        await self.async_ensure_tokens_valid()
        LOGGER.debug(
            "Getting Search Result `%s` for account `%s`",
            query.search,
            self.name,
        )

        search_result = await self.hass.async_add_executor_job(
            self.apis["public"].search,
            query.query_string,
            limit,
            0,
            query.item_types_string,
            self.country,
        )

        result = {}

        for item_type in query.item_types:
            key = f"{item_type}s"
            result[key] = [
                item
                for item in (search_result[key]["items"] or [])
                if item is not None
            ]

        return result

    async def async_categories(
        self,
        force: bool = False,
        limit: int = None,
    ) -> list[dict]:
        """Fetches the categories available for the account"""
        await self.async_ensure_tokens_valid()
        LOGGER.debug("Getting Browse Categories for account `%s`", self.name)

        dataset = self._datasets["categories"]

        async with dataset.lock:
            if force or dataset.is_expired():
                LOGGER.debug("Refreshing Browse Categories dataset")

                categories = await self._async_pager(
                    self.apis["public"].categories,
                    prepends=[self.country, None],
                    sub_layer="categories",
                    max_items=limit,
                )

                dataset.update(categories)
            else:
                LOGGER.debug("Using cached Browse Categories dataset")

        return self.categories

    async def async_liked_songs_count(self) -> int:
        """Returns the number of linked songs for an account."""
        await self.async_ensure_tokens_valid()

        dataset = self._datasets["liked_songs_count"]

        async with dataset.lock:
            if dataset.is_expired():
                LOGGER.debug("Refreshing liked songs count dataset")

                count = await self._async_get_count(
                    self.apis["public"].current_user_saved_tracks,
                )

                dataset.update({"total": count})
            else:
                LOGGER.debug("Using cached liked songs count dataset")

        return self.get_dataset("liked_songs_count")["total"]

    async def async_liked_songs(self, force: bool = False) -> list[str]:
        """Retrieves the list of uris of songs in the user liked songs."""
        await self.async_ensure_tokens_valid()
        LOGGER.debug("Getting saved tracks for account `%s`", self.name)

        dataset = self._datasets["liked_songs"]

        async with dataset.lock:
            if force or dataset.is_expired():
                LOGGER.debug("Refreshing liked songs dataset")

                liked_songs = await self._async_pager(
                    self.apis["public"].current_user_saved_tracks,
                )

                dataset.update(liked_songs)
            else:
                LOGGER.debug("Using cached liked songs dataset")

        return self.liked_songs

    async def async_like_media(self, uris: list[str]):
        """Adds a list of uris to the user's liked songs."""
        await self.async_ensure_tokens_valid()

        dataset = self._datasets["liked_songs"]
        count_dataset = self._datasets["liked_songs_count"]

        # Force expire the liked_songs datasets
        async with dataset.lock, count_dataset.lock:
            dataset.expires_at = 0
            count_dataset.expires_at = 0
            LOGGER.debug("Expired liked_songs datasets after adding new likes")

            await self.hass.async_add_executor_job(
                self.apis["public"].current_user_saved_tracks_add,
                uris,
            )

    async def async_unlike_media(self, uris: list[str]):
        """Removes a list of uris from the user's liked songs."""
        await self.async_ensure_tokens_valid()

        dataset = self._datasets["liked_songs"]
        count_dataset = self._datasets["liked_songs_count"]

        # Force expire the liked_songs datasets
        async with dataset.lock, count_dataset.lock:
            dataset.expires_at = 0
            count_dataset.expires_at = 0
            LOGGER.debug("Expired liked_songs datasets after removing likes")

            await self.hass.async_add_executor_job(
                self.apis["public"].current_user_saved_tracks_delete,
                uris,
            )
