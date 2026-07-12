# Player

Provides the active playback state for a Spotify account.

## Request

```json
{
    "id": 1,
    "type": "spotcast/player",
    "account": "01JDG07KSBTYWZGJSBJ1EW6XEF"
}
```

### `id` (int)

*Required*

The id of the transaction. Must be an increment of the last transaction id.

### `type` (str)

*Required*

The endpoint of the WebSocket to reach. Must be `spotcast/player`.

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
        "account": "01JDG07KSBTYWZGJSBJ1EW6XEF",
        "state": {
            "device": {
                "id": "12345",
                "is_active": true,
                "is_private_session": false,
                "is_restricted": false,
                "name": "foo",
                "type": "Computer",
                "volume_percent": 100,
                "supports_volume": true
            },
            "repeat_state": "context",
            "shuffle_state": false,
            "context": {
                "type": "album",
                "href": "https://api.spotify.com/v1/albums/1chw1DFmefTueG1VbNVoGN",
                "external_urls": {
                    "spotify": "https://open.spotify.com/album/1chw1DFmefTueG1VbNVoGN"
                },
                "uri": "spotify:album:1chw1DFmefTueG1VbNVoGN"
            },
            "timestamp": 1732541310670,
            "progress_ms": 76425,
            "is_playing": true,
            "item": {},
            "currently_playing_type": "track",
            "actions": {
                "disallows": {
                    "resuming": true
                }
            },
            "smart_shuffle": false
        }
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

> #### `account` (str)
>
> The id of the account used in the query.
>
> #### `state` (dict)
>
> The current playback state. See [Get Playback State](https://developer.spotify.com/documentation/web-api/reference/get-information-about-the-users-current-playback) for the fields. Returns an empty dictionary when there is no active playback.
>
