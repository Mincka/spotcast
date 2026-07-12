# Liked Media

Provides the list of liked media (tracks) for a user.

## Request

```json
{
    "id": 1,
    "type": "spotcast/liked_media",
    "account": "01JDG07KSBTYWZGJSBJ1EW6XEF"
}
```

### `id` (int)

*Required*

The id of the transaction. Must be an increment of the last transaction id.

### `type` (str)

*Required*

The endpoint of the WebSocket to reach. Must be `spotcast/liked_media`.

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
        "total": 5,
        "account": "01JDG07KSBTYWZGJSBJ1EW6XEF",
        "tracks": [
            "spotify:track:3n3Ppam7vgaVa1iaRUc9Lp",
            "spotify:track:6rqhFxbN4uN6t6z2p3xPQK",
            "spotify:track:7gBEnASdyC9XBZf51a0tpn",
            "spotify:track:3nYCh0PbdJ23V2Jp0CzJ8N",
            "spotify:track:0VjIjW4GlUZAMYd2vXMi3b"
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
> The number of liked tracks retrieved.
>
> #### `account` (str)
>
> The id of the account used in the query.
>
> #### `tracks` (list[str])
>
> The Spotify URIs of the liked tracks. Each entry is a track URI string. See [URI format](https://developer.spotify.com/documentation/web-api/concepts/spotify-uris-ids).
>
