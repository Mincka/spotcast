# Categories

Provides the list of Browse categories available for an account.

## Request

```json
{
    "id": 1,
    "type": "spotcast/categories",
    "account": "01JDG07KSBTYWZGJSBJ1EW6XEF",
    "limit": 10
}
```

### `id` (int)

*Required*

The id of the transaction. Must be an increment of the last transaction id.

### `type` (str)

*Required*

The endpoint of the WebSocket to reach. Must be `spotcast/categories`.

### `account` (str)

*Optional*

The `entry_id` of the account to use. Defaults to the default Spotcast account if not provided.

### `limit` (int)

*Optional*

Limits the number of categories retrieved. Retrieves all available categories if not provided.

## Response

```json
{
    "id": 1,
    "type": "result",
    "success": true,
    "result": {
        "total": 10,
        "account": "01JDG07KSBTYWZGJSBJ1EW6XEF",
        "categories": [
            {
                "id": "0JQ5DAt0tbjZptfcdMSKl3",
                "icon": "https://t.scdn.co/images/728ed47fc1674feb95f7ac20236eb6d7.jpeg",
                "name": "Made For You"
            },
            {
                "id": "0JQ5DAqbMKFNNuveavxU1i",
                "icon": "https://t.scdn.co/images/728ed47fc1674feb95f7ac20236eb6d7.jpeg",
                "name": "New Releases"
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
> Number of Browse categories retrieved.
>
> #### `account` (str)
>
> The id of the account used in the query.
>
> #### `categories` (list[dict])
>
> The list of Browse categories retrieved.
>
> > ##### `id` (str)
> >
> > The identifier of the Browse category.
> >
> > ##### `icon` (str)
> >
> > URL to the image used for the category in Spotify's apps.
> >
> > ##### `name` (str)
> >
> > The name of the Browse category.
> >
