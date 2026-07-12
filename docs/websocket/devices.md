# Devices

Provides the list of currently available Spotify Connect devices for an account.

## Request

```json
{
    "id": 1,
    "type": "spotcast/devices",
    "account": "01JDG07KSBTYWZGJSBJ1EW6XEF"
}
```

### `id` (int)

*Required*

The id of the transaction. Must be an increment of the last transaction id.

### `type` (str)

*Required*

The endpoint of the WebSocket to reach. Must be `spotcast/devices`.

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
        "total": 1,
        "account": "01JDG07KSBTYWZGJSBJ1EW6XEF",
        "devices": [
            {
                "id": "042ee68e1c57247fe3c214f1669e5a4933a9f6b4",
                "is_active": false,
                "is_private_session": false,
                "is_restricted": false,
                "name": "billabongvalley",
                "supports_volume": true,
                "type": "Computer",
                "volume_percent": 53
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
> Number of devices available for the account.
>
> #### `account` (str)
>
> The id of the account used in the query.
>
> #### `devices` (list[dict])
>
> The devices available for the account at the time of the transaction. These are the raw Spotify device objects.
>
> > ##### `id` (str)
> >
> > The Spotify ID of the device.
> >
> > ##### `is_active` (bool)
> >
> > `true` if the device is actively playing media.
> >
> > ##### `is_private_session` (bool)
> >
> > `true` if the device is currently in a private session.
> >
> > ##### `is_restricted` (bool)
> >
> > `true` if the device cannot be controlled through the API (Spotcast cannot control it).
> >
> > ##### `name` (str)
> >
> > The name of the device as shown in Spotify's apps.
> >
> > ##### `supports_volume` (bool)
> >
> > `true` if the device's volume can be controlled through the API.
> >
> > ##### `type` (str)
> >
> > The type of device.
> >
> > ##### `volume_percent` (int)
> >
> > An integer between `0` and `100` for the current volume percentage.
> >
