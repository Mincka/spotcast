<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/images/logo/white/128.png">
  <source media="(prefers-color-scheme: light)" srcset="./assets/images/logo/dark_gray/128.png">
  <img alt="Spotcast" src="https://raw.githubusercontent.com/Mincka/spotcast/main/assets/images/logo/green/128.png">
</picture>

------------------------------------------------------------------------------

[![release](https://img.shields.io/github/v/release/Mincka/spotcast?include_prereleases)](https://github.com/Mincka/spotcast/releases)
[![tests](https://github.com/Mincka/spotcast/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/Mincka/spotcast/actions/workflows/unittest.yml)
[![license](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](./LICENSE)
![maintenance](https://img.shields.io/maintenance/yes/2026.svg)

Spotcast is a Home Assistant custom integration that starts Spotify playback on an idle Chromecast or Spotify Connect device, so your automations can target both device families the same way.

> [!IMPORTANT]
> Spotcast requires a **Spotify Premium** account to work.

> [!WARNING]
> Some Spotcast features need permissions that Spotify does not grant to regular third-party applications. To obtain them, Spotcast authenticates one session under the identity of the official Spotify desktop application (this is the desktop authorization step during setup). This method is not officially supported by Spotify and may stop working without notice if Spotify changes its authentication systems. We do our best to adapt quickly when that happens, but temporary breakage is always possible.

> [!NOTE]
> This repository is the continuation of the original [fondberg/spotcast](https://github.com/fondberg/spotcast) project, created by Niklas Fondberg ([@fondberg](https://github.com/fondberg)) and maintained through v5 and the v6 rewrite by Felix Cusson ([@fcusson](https://github.com/fcusson)). Development now happens here, starting with the v6 release.

## Coming from the original fondberg/spotcast?

Welcome, and thanks for sticking with Spotcast. Whether you ran it for years on v4 or tried the v6 alphas, this is where the project lives now and it is actively maintained again. Here is how to come over depending on where you are:

- **If your old Spotcast (v4) stopped working** with login loops, reauthentication failures, or errors like `400 Bad Request` on `accounts.spotify.com/api/token` or `ServerTime`, that is not your setup: Spotify changed its authentication on their side and the old cookie-based method can no longer work. **The v6 rewrite is the fix.** It was only ever published as a pre-release on the original repository, so HACS never offered it to you as an update, which is exactly why moving here matters. v6 is a ground-up rewrite with a new setup flow (the old `sp_dc`/`sp_key` YAML is gone), so you will configure it once by following the [configuration guide](./docs/config/spotcast_configuration.md).
- **If you were already on a v6 alpha or beta**, switching here is a clean swap on the same major version: your accounts, tokens, entities and automations carry over untouched.

To move over in HACS: remove the existing Spotcast download from **HACS only** (do **not** delete the integration from *Settings -> Devices & Services*, that would erase your configuration), then add this repository as a [custom repository](#hacs-custom-repository) and download it. Home Assistant keys your configuration to the `spotcast` integration itself, not to the repository it came from, so a same-version reinstall picks your existing setup right back up. Restart Home Assistant when done.

## Project scope

Spotcast focuses on one thing and aims to do it well: **starting and transferring Spotify playback from Home Assistant automations**, including on devices that are not signed into your Spotify account (like Chromecast speakers). It intentionally keeps side features minimal.

If you are looking for comprehensive Spotify control from Home Assistant (full media player, browsing, favorites management, near-complete Web API coverage), have a look at [SpotifyPlus](https://github.com/thlucas1/homeassistantcomponent_spotifyplus) and its companion [SpotifyPlus Card](https://github.com/thlucas1/spotifyplus_card) - they complement Spotcast rather than compete with it.

## Installation

### HACS (custom repository)

> [!NOTE]
> Spotcast is **not yet available in the HACS default store**; submission is in progress. Until it lands, install it through HACS by adding this repository as a custom repository:

1. In Home Assistant, open **HACS**.
2. Open the menu (⋮ top right) and select **Custom repositories**.
3. Add `https://github.com/Mincka/spotcast` with type **Integration**.
4. Search for `Spotcast` in HACS and download it.
5. Restart Home Assistant.

Or use this direct link:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Mincka&repository=spotcast&category=integration)

### Manual installation

1. Download the latest release from the [releases page](https://github.com/Mincka/spotcast/releases) (or in GitHub, click the `<> Code` button and select `Download ZIP`).
2. Extract the archive.
3. Copy the `custom_components/spotcast/` folder into the `custom_components/` folder of your Home Assistant configuration directory.
4. Restart Home Assistant.

## Configuration

### Minimum Home Assistant version

Spotcast is compatible with Home Assistant `2026.4` and later.

### Official Spotify integration

The [Home Assistant Spotify integration](https://www.home-assistant.io/integrations/spotify/) is **not required** by Spotcast, except for media browsing. You can set it up here:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=spotify)

### Setup

Follow the [configuration guide](./docs/config/spotcast_configuration.md) or click the link below to start the config flow (links to the relevant documentation are provided directly in the configuration steps):

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=spotcast)

## Actions

| Action                                                                 | Description                                                                                          |
| :---                                                                   | :---                                                                                                 |
| [spotcast.play_media](./docs/services/play_media.md)                   | Starts playback on a Chromecast or Spotify Connect device using the provided URI as context.         |
| [spotcast.play_liked_songs](./docs/services/play_liked_songs.md)       | Starts playback on a Chromecast or Spotify Connect device using the user's saved tracks as context.  |
| [spotcast.play_dj](./docs/services/play_dj.md)                         | Starts playback on a Chromecast or Spotify Connect device using the DJ feature as context.           |
| [spotcast.play_from_search](./docs/services/play_from_search.md)       | Starts playback on a Chromecast or Spotify Connect device using a search result as context.          |
| [spotcast.play_custom_context](./docs/services/play_custom_context.md) | Starts playback on a Chromecast or Spotify Connect device using a list of URIs as context.           |
| [spotcast.play_saved_episodes](./docs/services/play_saved_episodes.md) | Plays the podcast episodes from the user's `Saved Episodes` list.                                    |
| [spotcast.transfer_playback](./docs/services/transfer_playback.md)     | Transfers the active or most recent playback to the provided device.                                 |
| [spotcast.add_to_queue](./docs/services/add_to_queue.md)               | Adds songs to the playback queue. Fails and returns an error if there is no active playback.         |
| [spotcast.like_media](./docs/services/like_media.md)                   | Adds a list of media URIs to the user's liked content.                                               |

### Data

Playback actions accept a common `data` section. Here is a list of the common options; some actions have additional options, see each action's documentation for details.

| Option          | Type                      | Default | Description                                                                                                          |
| :---:           | :---:                     | :---:   | :---                                                                                                                 |
| `position`      | `positive_float`          | `0.000` | The position (in seconds) at which to start playback of the first item in the context.                              |
| `offset`        | `positive_int`            | `0`     | The item in the context to start playback at. Zero based and cannot be negative.                                     |
| `volume`        | `int`, `range 0-100`      | `null`  | The volume percentage (as an integer) to start playback at. Volume is kept unchanged if `null`.                      |
| `repeat`        | `track \| context \| off` | `null`  | The repeat mode. Kept unchanged if `null`.                                                                           |
| `shuffle`       | `bool`                    | `null`  | Sets the playback to shuffle if `True`. Kept unchanged if `null`.                                                    |
| `limit`         | `positive_int`            | `null`  | The maximum number of items retrieved from a Spotify API endpoint. Retrieves all items if `null`.                    |
| `random`        | `bool`                    | `False` | Starts the context playback at a random item. Only available for albums, playlists and custom contexts.              |
| `track_context` | `track \| album \| context URI` | `album` | Sets the context of a track. With `album`, the rest of the album plays after the song ends; with `track`, playback stops; with an album or playlist URI (e.g. `spotify:playlist:xxxx`), the track plays inside that context and the context continues afterwards. The track must be part of the context. |

## Entities

Spotcast creates multiple entities for each Spotify account.

### Sensors

| Example name                        | Description                                                                            | States          |
| :---                                | :---                                                                                   | :---:           |
| `sensor.[...]_spotify_profile`      | Reports the profile of the Spotify account. Provides attributes linked to the account. | `ok\|unknown`   |
| `sensor.[...]_spotify_devices`      | Tracks the number of devices available for the account.                                | `int`           |
| `sensor.[...]_spotify_followers`    | Tracks the number of followers the account has.                                        | `int`           |
| `sensor.[...]_spotify_liked_songs`  | Tracks the number of songs liked by the account.                                       | `int`           |
| `sensor.[...]_spotify_playlists`    | Tracks the number of playlists created by the account.                                 | `int`           |
| `sensor.[...]_spotify_account_type` | Diagnostic sensor that reports the type of account connected through Spotcast.         | `user`          |
| `sensor.[...]_spotify_product`      | Diagnostic sensor that reports the subscription level of the account.                  | `premium\|free` |

### Binary sensors

| Example name                                      | Description                                                                                    |
| :---                                              | :---                                                                                           |
| `binary_sensor.[...]_is_default_spotcast_account` | Diagnostic sensor that confirms if the account is currently the default account for Spotcast.  |
| `binary_sensor.[...]_spotify_profile_malfunction` | Diagnostic error sensor that turns on when a connection issue happens with the API.            |

### Media players

Spotcast creates `media_player` entities and devices to represent Spotify Connect devices linked to a Spotcast account. These media players do not implement any playback functionality and are meant to be used in action calls when starting playback on a Spotify Connect device.

## WebSocket API

Spotcast provides multiple WebSocket API endpoints, used for example by companion frontend cards:

| Endpoint                                                    | Description                                                                                                                                     |
| :---                                                        | :---                                                                                                                                            |
| [`spotcast/accounts`](./docs/websocket/accounts.md)         | Provides a list of accounts linked to Spotcast.                                                                                                 |
| [`spotcast/castdevices`](./docs/websocket/cast_devices.md)  | Provides a list of Chromecast devices available in Home Assistant.                                                                              |
| [`spotcast/categories`](./docs/websocket/categories.md)     | Provides a list of [Browse categories](https://developer.spotify.com/documentation/web-api/reference/get-categories) an account has access to.  |
| [`spotcast/devices`](./docs/websocket/devices.md)           | Provides a list of Spotify Connect devices available to the account.                                                                            |
| [`spotcast/liked_media`](./docs/websocket/liked_media.md)   | Provides the list of liked tracks for an account.                                                                                               |
| [`spotcast/player`](./docs/websocket/player.md)             | Provides the playback state of an account.                                                                                                      |
| [`spotcast/playlists`](./docs/websocket/playlists.md)       | Provides the list of the user's playlists.                                                                                                      |
| [`spotcast/search`](./docs/websocket/search.md)             | Searches Spotify for playlists, tracks, albums or artists.                                                                                      |
| [`spotcast/tracks`](./docs/websocket/tracks.md)             | Provides the list of tracks in a playlist.                                                                                                      |
| [`spotcast/view`](./docs/websocket/view.md)                 | Provides the list of playlists from a Spotify view (e.g. `recently-played`).                                                                    |

## Upgrading from v5

The v6 rewrite changed both the configuration flow and the action names:

- Configuration no longer uses `sp_dc`/`sp_key` cookies in YAML. Accounts are set up through the UI with OAuth and a one-time desktop authorization. Follow the [configuration guide](./docs/config/spotcast_configuration.md).
- The `spotcast.start` service was replaced by a set of dedicated actions. The closest equivalent to `spotcast.start` is [`spotcast.play_media`](./docs/services/play_media.md), with most of its former options now under the `data` section.
- `spotcast.play_category` was removed, following the deprecation of the corresponding Spotify Web API endpoints.

## Related projects

- [SpotifyPlus](https://github.com/thlucas1/homeassistantcomponent_spotifyplus) and [SpotifyPlus Card](https://github.com/thlucas1/spotifyplus_card) - a comprehensive Spotify integration and card, recommended when you need full Spotify control beyond starting playback.

## Contributing

Contributions are welcome! Please read the [contributing guidelines](./CONTRIBUTING.md) for the branch model, development setup and quality gates (test coverage and pylint score).

## Credits

Spotcast was created by [Niklas Fondberg](https://github.com/fondberg), who passed away in 2024. This project continues in his memory. It was maintained, including the complete v5/v6 rewrite, by [Felix Cusson](https://github.com/fcusson). Thanks to them and to all the [contributors](https://github.com/Mincka/spotcast/graphs/contributors) who made this project possible. It is now maintained by [Julien Ehrhart](https://github.com/Mincka).

## License

[Apache 2.0](./LICENSE) - see also the [NOTICE](./NOTICE) file.
