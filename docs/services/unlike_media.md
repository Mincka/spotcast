# Unlike Media

Remove a list of Spotify URIs from a specific Spotify account's library.

## Action

```yaml
action: spotcast.unlike_media
data:
    spotify_uris:
        - spotify:track:1yuxSH79Cj1nGqN1AKD9p5
        - spotify:track:2dbJ0mn0vTVz6mc3rk2t77
    account: 01JDG07KSBTYWZGJSBJ1EW6XEF
```
### `spotify_uris` (list[str])

*Required*

A list of Spotify track URIs or URLs to remove from the library. This is the counterpart to [`like_media`](./like_media.md).

### `account` (str)

*Optional*

The `entry_id` of the account to use for Spotcast. If empty, the default Spotcast account is used.
