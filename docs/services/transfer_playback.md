# Play Transfer Playback

Transfers the active or most recent playback of an account to a different media player

## Action

```yaml
action: spotcast.transfer_playback
data:
    media_player:
        entity_id: media_player.foo
    account: 01JDG07KSBTYWZGJSBJ1EW6XEF
    data:
        repeat: context
```

### `media_player` (dict)

*Required*

Let the user select a compatible device on which to start the playback. **_Must be a single device_**. A Chromecast speaker group (for example a Google Cast group) is a valid target and counts as a single device.

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

> [!NOTE]
> **Spotify editorial/algorithmic playlists** (the `spotify:playlist:37i9…` IDs): when rebuilding playback, the currently playing track's URI is passed directly as the offset, so playback resumes at that track without paginating through the whole context.
