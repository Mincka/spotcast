# Playlists

Provides the list of the user's playlists.

## Request

```json
{
    "id": 1,
    "type": "spotcast/playlists",
    "account": "01JDG07KSBTYWZGJSBJ1EW6XEF",
    "limit": 20
}
```

### `id` (int)

*Required*

The id of the transaction. Must be an increment of the last transaction id.

### `type` (str)

*Required*

The endpoint of the WebSocket to reach. Must be `spotcast/playlists`.

### `account` (str)

*Optional*

The `entry_id` of the account to use. Defaults to the default Spotcast account if not provided.

### `limit` (int)

*Optional*

Limits the number of playlists retrieved. Retrieves all playlists if not provided.

## Response

```json
{
    "id": 1,
    "type": "result",
    "success": true,
    "result": {
        "total": 20,
        "account": "01JDG07KSBTYWZGJSBJ1EW6XEF",
        "category": "user",
        "playlists": [
            {},
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
> The number of playlists retrieved.
>
> #### `account` (str)
>
> The id of the account used in the query.
>
> #### `category` (str)
>
> Always `user`. Kept for backward compatibility with earlier versions that supported Browse category drilldown (removed after Spotify deprecated the category playlists endpoint).
>
> #### `playlists` (list[dict])
>
> The user's playlists. These are the raw Spotify playlist objects; see [Get Playlist](https://developer.spotify.com/documentation/web-api/reference/get-playlist) for the fields.
>
