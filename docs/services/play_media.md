# Play Media

Play spotify media on Spotcast compatible device

## Action

```yaml
action: spotcast.play_media
data:
    media_player:
        entity_id: media_player.foo
    spotify_uri: spotify:album:1chw1DFmefTueG1VbNVoGN
    account: 01JDG07KSBTYWZGJSBJ1EW6XEF
    data:
        repeat: context
```

### `media_player` (dict)

*Optional*

Let the user select a compatible device on which to start the playback. **_Must be a single device_**. A Chromecast speaker group (for example a Google Cast group) is a valid target and counts as a single device.

### `spotify_uri` (str)

*Required*

The Spotify URI or URL used for the context in the playback. In the case of a track URI, the context will become the album of the track, but set to the correct position of the track in the album. This behavior can be changed with the `track_context` option in `data`: `track` plays only the song, `album` (default) plays the rest of the album afterwards, and an album or playlist URI (e.g. `spotify:playlist:xxxx`) plays the track inside that context, continuing with the context afterwards. The track must be part of the provided context.

### `account` (str)

*Optional*

The `entry_id` of the account to use for Spotcast. If empty, the default Spotcast account is used.

### `data` (dict)

*Optional*

Set of additional settings to apply when starting the playback. The available options are:

| Option     | type                      | default | description                                                                                                                                 |
| :---:      | :---:                     | :---:   | :---                                                                                                                                        |
| `position` | `positive_float`          | `0.000` | The position to start playback (in seconds) of where to start the playback of the first item in the context                                 |
| `offset`   | `positive_int`            | `0`     | The item in the context to start the playback at. The position is zero based and cannot be negative. Is ignored in the case of a track URI. |
| `volume`   | `int`, `range 0-100`      | `null`  | The percentage (as an integer of the percentage value) to start plaback at. Volume is kept unchanged if `null`                              |
| `repeat`   | `track \| context \| off` | `null`  | The repeat mode is kept the same if `null`                                                                                                  |
| `shuffle`  | `bool`                    | `null`  | Sets the playback to shuffle if `True`. Is kept unchanged if `null`.                                                                        |
| `random`   | `bool`                    | `False` | Sets the context playback to a random song of the context. Only available for albums, playlists and custom contexts |
| `track_context` | `track \| album \| uri` | `album` | Only used when `spotify_uri` is a track. `track` plays only the song; `album` plays the song's album starting at the song; an album or playlist URI (e.g. `spotify:playlist:xxxx`) plays the track inside that context, continuing with it afterwards. The track must be part of the provided context. |

> [!NOTE]
> **Spotify editorial/algorithmic playlists** (the `spotify:playlist:37i9…` IDs - Daily Mix, Discover Weekly, Release Radar, song radios, etc.): Spotify no longer serves these playlists' contents through the public Web API, so `random` cannot read the track count from there. For them it resolves the real track count through Spotify's internal metadata endpoint and picks a random start across the **whole playlist**. Only if that endpoint is unavailable does it fall back to a random start within the first 25 tracks (emitted as a log warning). Regular playlists are unaffected.

## Examples

### Play an album

```yaml
action: spotcast.play_media
data:
    media_player:
        entity_id: media_player.living_room
    spotify_uri: spotify:album:1chw1DFmefTueG1VbNVoGN
```

### Play only a single track

A track URI plays inside its album by default. Set `track_context: track` to play just the song.

```yaml
action: spotcast.play_media
data:
    media_player:
        entity_id: media_player.living_room
    spotify_uri: spotify:track:5J7j5w4UUMnGJ21rYVQfob
    data:
        track_context: track
```

### Play a track inside a specific playlist

Start on a track but keep the playlist going afterwards by passing the playlist URI as `track_context`. The track must be part of that playlist.

```yaml
action: spotcast.play_media
data:
    media_player:
        entity_id: media_player.living_room
    spotify_uri: spotify:track:5J7j5w4UUMnGJ21rYVQfob
    data:
        track_context: spotify:playlist:37i9dQZF1DXcBWIGoYBM5M
```

### Start a playlist at a random track

```yaml
action: spotcast.play_media
data:
    media_player:
        entity_id: media_player.living_room
    spotify_uri: spotify:playlist:37i9dQZF1DXcBWIGoYBM5M
    data:
        random: true
```
