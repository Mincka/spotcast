# Cast Devices

Provides the list of Chromecast devices available in Home Assistant.

## Request

```json
{
    "id": 1,
    "type": "spotcast/castdevices"
}
```

### `id` (int)

*Required*

The id of the transaction. Must be an increment of the last transaction id.

### `type` (str)

*Required*

The endpoint of the WebSocket to reach. Must be `spotcast/castdevices`.

## Response

```json
{
    "id": 1,
    "type": "result",
    "success": true,
    "result": {
        "total": 2,
        "devices": [
            {
                "entity_id": "media_player.reveil",
                "uuid": "b4d1c2e0-0000-0000-0000-000000000000",
                "model_name": "Lenovo Smart Clock",
                "friendly_name": "Reveil",
                "manufacturer": "LENOVO"
            },
            {
                "entity_id": "media_player.cuisine",
                "uuid": "a1b2c3d4-0000-0000-0000-000000000000",
                "model_name": "Google Home",
                "friendly_name": "Cuisine",
                "manufacturer": "Google Inc."
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
> Number of Chromecast devices available in Home Assistant.
>
> #### `devices` (list[dict])
>
> The list of Chromecast devices.
>
> > ##### `entity_id` (str)
> >
> > The entity id of the device in Home Assistant.
> >
> > ##### `uuid` (str)
> >
> > The universally unique identifier of the Chromecast device.
> >
> > ##### `model_name` (str)
> >
> > The model of the Chromecast device as reported by itself.
> >
> > ##### `friendly_name` (str)
> >
> > The name of the device in Google services.
> >
> > ##### `manufacturer` (str)
> >
> > The manufacturer of the Chromecast device as reported by itself.
> >
