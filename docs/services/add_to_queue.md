# Add To Queue

Adds a list of Spotify URIs to the account's playback queue.

## Action

```yaml
action: spotcast.add_to_queue
data:
    spotify_uris:
        - spotify:track:03Vh87Tg6boENhCNstwKX2
        - spotify:track:2GfQhXyoUXYTkMHDXJhCU5
    account: 01JDG07KSBTYWZGJSBJ1EW6XEF
```

### `spotify_uris` (list[str])

*Required*

A list of spotify URI or URL to add to the queue of the current playback

### `account` (str)

*Optional*

The `entry_id` of the account to use for Spotcast. If empty, the default Spotcast account is used.
