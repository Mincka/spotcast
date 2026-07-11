# Changelog

This repository is the continuation of the original [fondberg/spotcast](https://github.com/fondberg/spotcast) project. For the history of releases prior to v6, see the [original project's releases](https://github.com/fondberg/spotcast/releases).

## v6.0.0 (upcoming)

Spotcast v6 is a complete rewrite of the integration. It requires **Home Assistant 2026.4 or newer**.

### Highlights

- **New configuration flow**: accounts are set up through the UI using OAuth application credentials and a one-time desktop token relay. The `sp_dc`/`sp_key` YAML configuration is gone. See the [configuration guide](./docs/config/spotcast_configuration.md).
- **New actions**: the `spotcast.start` service is replaced by dedicated actions - `play_media`, `play_liked_songs`, `play_dj`, `play_from_search`, `play_custom_context`, `play_saved_episodes`, `transfer_playback`, `add_to_queue` and `like_media`.
- **WebSocket API**: endpoints for accounts, devices, cast devices, categories, playlists, tracks, liked media, search, views and playback state, usable by frontend cards.
- **Entities**: sensors, binary sensors and media players are created for each Spotify account.
- **Multi-account support** with a default account and per-call account selection.

### Changes consolidated from the original repository's pending pull requests

- Removed deprecated Spotify Web API usage (audio features, category playlists - `spotcast.play_category` is gone) and modernized the integration for recent Home Assistant and Python versions ([fondberg/spotcast#610](https://github.com/fondberg/spotcast/pull/610)).
- Graceful handling of Spotify 404 responses on editorial/algorithmic playlists ([fondberg/spotcast#611](https://github.com/fondberg/spotcast/pull/611)).
- Dead code cleanup ([fondberg/spotcast#612](https://github.com/fondberg/spotcast/pull/612)).
- Device names are sanitized into valid entity IDs, fixing accounts and devices with non-ASCII characters ([fondberg/spotcast#614](https://github.com/fondberg/spotcast/pull/614)).
- `play_from_search` no longer fails when Spotify search results contain null entries ([fondberg/spotcast#616](https://github.com/fondberg/spotcast/pull/616)).

### Removed

- The legacy cookie-based (`sp_dc`/`sp_key`) private API machinery is gone entirely: v6 authenticates through OAuth application credentials and a desktop token. This also removes the `pyotp` dependency and the cookie-extraction documentation.

### Project changes

- The project is now maintained at [Mincka/spotcast](https://github.com/Mincka/spotcast); see the [NOTICE](./NOTICE) file for attribution.
- The PowerShell relay server script is now part of the repository (`scripts/relay_server.ps1`).
- Installation is done through HACS as a custom repository until the project is accepted into the HACS default store.
