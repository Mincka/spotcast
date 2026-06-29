"""Utility functions for interacting with Spotify"""

import logging
from contextlib import contextmanager

_SPOTIPY_LOGGER = logging.getLogger("spotipy.client")


def select_image_url(images: list[dict]) -> str:
    """Returns the highest resolution image available according to the
    list of images provided

    Args:
        - images(list[dict]): the list of images as returned by a
            Spotify API endpoint. Expected to have a `height`, `width`,
            and `url` key.

    Returns:
        - str: The URL of the highest resolution image
    """
    image_url = None
    max_area = 0

    for image in images:

        width = image.get("width")
        height = image.get("height")

        # assume top image best fit when no size provided
        if any(x is None for x in (width, height)):
            image_url = image["url"]
            break

        area = image["width"] * image["height"]

        if area > max_area:
            image_url = image["url"]
            max_area = area

    return image_url


def url_to_uri(url: str) -> str:
    """converts a url to a spotify uri"""

    # if already a uri skip
    if url.startswith("spotify:"):
        return url

    # remove the protocol section
    url = url.split("://", maxsplit=1)[-1]

    # remove query if present
    url = url.rsplit("?", maxsplit=1)[0]

    # split items on slashes
    elems = url.split('/')

    # replace first item with spotify
    elems[0] = "spotify"

    uri = ":".join(elems)

    return uri


@contextmanager
def suppress_playlist_404_logs():
    """Silence spotipy's ERROR log for an expected playlist 404.

    Spotify returns 404 for its own editorial/algorithmic playlists
    (`37i9...`) when their content is requested through the Web API.
    spotipy logs the HTTP error itself (`spotipy/client.py`) *before*
    raising `SpotifyException`, so a `try/except` around the call cannot
    prevent the noisy ERROR line. Spotcast expects and handles this 404,
    so drop only that record for the duration of the call. Any other
    spotipy error (including non-playlist 404s) still logs normally.
    """

    def _drop_expected_404(record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return not ("returned 404" in message and "playlists/" in message)

    _SPOTIPY_LOGGER.addFilter(_drop_expected_404)

    try:
        yield
    finally:
        _SPOTIPY_LOGGER.removeFilter(_drop_expected_404)
