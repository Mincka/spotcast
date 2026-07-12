# Tracks

Provides the list of tracks from a specified playlist.

## Request

```json
{
    "id": 1,
    "type": "spotcast/tracks",
    "playlist_id": "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",
    "account": "01JDG07KSBTYWZGJSBJ1EW6XEF"
}
```

### `id` (int)

*Required*

The id of the transaction. Must be an increment of the last transaction id.

### `type` (str)

*Required*

The endpoint of the WebSocket to reach. Must be `spotcast/tracks`.

### `playlist_id` (str)

*Required*

The Spotify ID or URI of the playlist whose tracks are retrieved. Accepts a full URI such as `spotify:playlist:37i9dQZF1DXcBWIGoYBM5M` or just the ID (`37i9dQZF1DXcBWIGoYBM5M`).

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
        "tracks": [
            {
                "id": "5J7j5w4UUMnGJ21rYVQfob",
                "name": "The Nights",
                "uri": "spotify:track:5J7j5w4UUMnGJ21rYVQfob",
                "album": {},
                "artists": [
                    {},
                    {}
                ]
            },
            {}
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
> The number of tracks retrieved.
>
> #### `account` (str)
>
> The id of the account used in the query.
>
> #### `tracks` (list[dict])
>
> The tracks retrieved from the playlist. Each track includes:
>
> > ##### `id` (str)
> >
> > Spotify's unique ID for the track.
> >
> > ##### `name` (str)
> >
> > The name of the track.
> >
> > ##### `uri` (str)
> >
> > The Spotify URI for the track. See [URI format](https://developer.spotify.com/documentation/web-api/concepts/spotify-uris-ids).
> >
> > ##### `album` (dict)
> >
> > Information about the album the track belongs to. See [Get playlist items](https://developer.spotify.com/documentation/web-api/reference/get-playlists-tracks).
> >
> > ##### `artists` (list[dict])
> >
> > The artists who contributed to the track. See [Get playlist items](https://developer.spotify.com/documentation/web-api/reference/get-playlists-tracks).
> >
