# Playlists

Provides the list of the user's playlists

## Request

```json
{
    "id": 7,
    "type": "spotcast/playlists",
    "account": "01JDG07KSBTYWZGJSBJ1EW6XEF",
    "limit": 20
}
```

### `id` (int)

The id of the transaction. Must be an increment of the last transaction id.

### `type` (str)

The endpoint of the websocket to reach. Must be `spotcast/playlists`

### `account` (str)

*Optional*

The entry id of the account used to get the active playback state. Defaults to the default spotcast account if not provided.

### `limit` (int)

*Optional*

Sets a limit to the number of playlists to retrieve

## Response

```json
{
    "id": 7,
    "type": "result",
    "result": {
        "total": 20,
        "account": "01JDG07KSBTYWZGJSBJ1EW6XEF",
        "category": "user",
        "playlists": [
            {...},
            {...}
        ]
    }
}
```

### `id` (int)

The id provided in the request

### `type` (str)

Always `result` on a successful request.

### `success` (bool)

True if the transaction was successful.

### `result` (dict)

The result of the transaction

> #### `total` (int)
> 
> The total number of playlists retrieved
>
> #### `account` (str)
>
> The account used in the query
>
> #### `category` (str)
>
> Always `user`. Kept for backward compatibility with earlier versions that supported Browse Category drilldown (removed after Spotify deprecated the category playlists endpoint).
> 
> #### `playlists` (list[dict])
> 
> List of the user's playlists. See [Get Playlist](https://developer.spotify.com/documentation/web-api/reference/get-playlist) for details about the fields
