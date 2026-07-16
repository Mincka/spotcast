"""Shared dataset and pagination helpers for the Spotify account.

Classes:
    PagingMixin
"""


class PagingMixin:  # pylint: disable=too-few-public-methods
    """Dataset access and Spotify pagination infrastructure shared by
    the content-reading mixins."""

    def get_dataset(self, name: str) -> list | dict:
        """Retrieves a specific dataset."""
        return self._datasets[name].data

    @staticmethod
    def _id_from_uri(uri: str) -> str:
        """extracts the id from a uri"""
        return uri.rsplit(":", maxsplit=1)[-1]

    async def _async_get_count(
        self,
        function: callable,
        prepends: list = None,
        appends: list = None,
        sub_layer: str = None,
    ) -> int:
        """Returns the number of item in a specific pagination

        Args:
            - function(callable): the function to call to retrieve
                content. Must be able to take a `limit` and `offset`
                arguments.
            - preppends: arguments to pass to the function on
                each call before the limit and offset
            - appends: arguments to pass to the function on
                each call after the limit and offset
            - sub_layer(str, optional): sub key in the response
                containing the pagination. Use the response as a
                pagination if None. Defaults to None.

        Returns:
            - int: the number of items in the pagination
        """
        prepends = [] if prepends is None else prepends
        appends = [] if appends is None else appends
        arguments = [*prepends, 1, 0, *appends]

        result = await self.hass.async_add_executor_job(
            function,
            *arguments,
        )

        if sub_layer is not None:
            result = result[sub_layer]

        return result["total"]

    # The pager exposes every paging knob of the Spotify API in one
    # helper, so the argument count is inherent to it.
    async def _async_pager(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        function: callable,
        prepends: list = None,
        appends: list = None,
        limit: int = 50,
        sub_layer: str = None,
        max_items: int = None,
    ) -> list[dict]:
        """Retrieves data from an api endpoint using a paging
        generator logic

        Args:
            - function(callable): the function to call to retrieve
                content. Must be able to take a `limit` and `offset`
                arguments.
            - preppends: arguments to pass to the function on
                each call before the limit and offset
            - appends: arguments to pass to the function on
                each call after the limit and offset
            - limit(int, optional): the maximum number of items to
                retrieve in a single call, defaults to 50
            - sub_layer(str, optional): sub key in the response
                containing the pagination. Use the response as a
                pagination if None. Defaults to None.
            - max_items(int, optional): the maximum number of items to
                retrieve. Retrieve all items if None. Defaults to None.

        Returns:
            - Generator[list[dict], None, None]
        """
        offset = 0
        items = []
        total = max_items
        prepends = [] if prepends is None else prepends
        appends = [] if appends is None else appends

        while total is None or len(items) < total:
            arguments = [*prepends, limit, offset, *appends]

            result = await self.hass.async_add_executor_job(
                function, *arguments
            )

            if sub_layer is not None:
                result = result[sub_layer]

            if total is None:
                total = result["total"]

            current_items = result["items"]

            if (delta := total - (len(items) + len(result["items"]))) < 0:
                current_items = current_items[:delta]

            items.extend(current_items)
            offset = len(items)

        items = [x for x in items if x is not None]

        return items
