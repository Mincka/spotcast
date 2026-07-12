# Accounts

Provides the list of Spotify accounts currently managed by Spotcast.

## Request

```json
{
    "id": 1,
    "type": "spotcast/accounts"
}
```

### `id` (int)

*Required*

The id of the transaction. Must be an increment of the last transaction id.

### `type` (str)

*Required*

The endpoint of the WebSocket to reach. Must be `spotcast/accounts`.

## Response

```json
{
    "id": 1,
    "type": "result",
    "success": true,
    "result": {
        "total": 2,
        "accounts": [
            {
                "entry_id": "01JDG07KSBTYWZGJSBJ1EW6XEF",
                "spotify_id": "foo",
                "spotify_name": "Foo",
                "is_default": true,
                "country": "CA"
            },
            {
                "entry_id": "01JDG0ZMDFEN2GDPVHV55R0X4P",
                "spotify_id": "bar",
                "spotify_name": "Bar",
                "is_default": false,
                "country": "CA"
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
> Total number of accounts currently managed by Spotcast.
>
> #### `accounts` (list[dict])
>
> The list of accounts managed by Spotcast.
>
> > ##### `entry_id` (str)
> >
> > The identifier of the configuration entry for the account.
> >
> > ##### `spotify_id` (str)
> >
> > The Spotify identifier of the account.
> >
> > ##### `spotify_name` (str)
> >
> > The display name for the account in Spotify.
> >
> > ##### `is_default` (bool)
> >
> > `true` if the account is used as the default for Spotcast services and WebSocket endpoints.
> >
> > ##### `country` (str)
> >
> > The [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) country code from the account profile.
> >
