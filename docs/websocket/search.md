# Search

Search for playlists, tracks, albums, or artists based on a query.

## Request

```json
{
    "id": 1,
    "type": "spotcast/search",
    "query": "rock",
    "search_type": "playlist",
    "limit": 10,
    "account": "01JDG07KSBTYWZGJSBJ1EW6XEF"
}
```

### `id` (int)

*Required*

The id of the transaction. Must be an increment of the last transaction id.

### `type` (str)

*Required*

The endpoint of the WebSocket to reach. Must be `spotcast/search`.

### `query` (str)

*Required*

The search query string. Any term such as a track name, album, artist, playlist name, or genre.

### `search_type` (str)

*Optional*

The type of item to search for. One of `playlist`, `track`, `album`, or `artist`. Defaults to `playlist`.

### `limit` (int)

*Optional*

The maximum number of results to retrieve. Defaults to `10`.

### `account` (str)

*Optional*

The `entry_id` of the account to use. Defaults to the default Spotcast account if not provided.

## Response

```json
{
    "id": 1,
    "type": "result",
    "success": true,
    "result": {
        "total": 2,
        "account": "01JDG07KSBTYWZGJSBJ1EW6XEF",
        "playlists": [
            {
                "id": "37i9dQZF1DXcBWIGoYBM5M",
                "name": "Rock Classics",
                "uri": "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",
                "description": "Classic rock hits",
                "icon": "https://link_to_image.com"
            },
            {
                "id": "37i9dQZF1DX4UtD7rx6U8w",
                "name": "Indie Rock",
                "uri": "spotify:playlist:37i9dQZF1DX4UtD7rx6U8w",
                "description": "Indie rock tracks",
                "icon": "https://link_to_image.com"
            }
        ]
    }
}
```

### `id` (int)

The id provided in the request.

### `type` (str)

Always `result` on a successful request.

### `success` (bool)

`true` if the transaction was successful.

### `result` (dict)

The result of the transaction.

> #### `total` (int)
>
> The number of results retrieved.
>
> #### `account` (str)
>
> The id of the account used in the query.
>
> #### `playlists` (list[dict])
>
> The search results. The key name depends on `search_type` and can be `playlists`, `tracks`, `albums`, or `artists`.
>
> > ##### `id` (str)
> >
> > The Spotify ID of the result.
> >
> > ##### `name` (str)
> >
> > The name of the playlist, track, album, or artist.
> >
> > ##### `uri` (str)
> >
> > The Spotify URI of the result. See [URI format](https://developer.spotify.com/documentation/web-api/concepts/spotify-uris-ids).
> >
> > ##### `description` (str)
> >
> > A description of the result, if available.
> >
> > ##### `icon` (str)
> >
> > A URL to an image for the result, if available.
> >
