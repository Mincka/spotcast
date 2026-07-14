# Changelog

This repository is the continuation of the original [fondberg/spotcast](https://github.com/fondberg/spotcast) project. For the history of releases prior to v6, see the [original project's releases](https://github.com/fondberg/spotcast/releases). Releases v6.3.0 through v6.5.2 are documented in the [GitHub release notes](https://github.com/Mincka/spotcast/releases).

## v6.5.3 (unreleased, testable as v6.5.3-beta.2)

### Fixes

- The playlists and liked songs count lookups are cached (5 minutes at the default refresh rate) instead of hitting the Spotify API on every update cycle, cutting steady-state API calls per account by roughly 40%. Liking or unliking media refreshes the cached count on the next cycle ([#54](https://github.com/Mincka/spotcast/issues/54)).
- When Spotify's API returns repeated server errors, the coordinator now reports "Spotify API temporarily unavailable (server errors)" instead of echoing the misleading `http status: 429` that the spotipy library hard-codes on retry exhaustion ([#54](https://github.com/Mincka/spotcast/issues/54), [spotipy-dev/spotipy#805](https://github.com/spotipy-dev/spotipy/issues/805)). Genuine rate limits keep the previous message.
- A failed refresh logs one error instead of two: the profile malfunction binary sensor no longer duplicates the coordinator's error line ([#54](https://github.com/Mincka/spotcast/issues/54)).
- The stale-device purge survives Home Assistant restarts (unavailability timestamps are persisted) and now also removes devices left over from previous Spotcast versions once they exceed the timeout ([#56](https://github.com/Mincka/spotcast/issues/56)).
- System health no longer leaks Spotify account ids or usernames into bug reports: accounts are reported as `Account 1`, `Account 2`, and so on.
- The `Device Registration Endpoint` system health check reported `unreachable` for everyone: it passed a bare hostname instead of a URL, so the request never started. It now checks the full address.

### Changes

- New per-account options: the number of days before unavailable devices are removed (default 7, 0 = immediately), and a device filter (deny or allow mode, with case-insensitive name patterns such as `*Jam*`) controlling which Spotify Connect devices get a `media_player` entity ([#56](https://github.com/Mincka/spotcast/issues/56)). See the [configuration guide](./docs/config/spotcast_configuration.md#integration-options).
- Migrated off the Spotify Web API endpoints removed by the [February 2026 platform changes](https://developer.spotify.com/documentation/web-api/references/changes/february-2026), which are rejected for Spotify applications created after 2026-02-11 ([#57](https://github.com/Mincka/spotcast/issues/57)): `like_media`/`unlike_media` now use `/me/library`, and playlist track listing uses `/playlists/{id}/items`. Both replacements also work for older applications.
- Removed the unused artist top-tracks helper; its endpoint was removed by Spotify with no replacement.

### Deprecations

- The `spotcast/categories` WebSocket endpoint is **deprecated**: Spotify removed Browse categories with no replacement for applications created after 2026-02-11 (older applications are grandfathered for now). The endpoint returns an empty list with a warning instead of raising for applications without access, and will be removed in a future release once grandfathered applications lose access.

## v6.2.0 (2026-07-12)

### Fixes

- Reauthentication no longer crashes on accounts created by older versions: legacy or malformed config entries missing `external_api` fields now fall back gracefully and show the reauth form instead of raising ([fondberg/spotcast#571](https://github.com/fondberg/spotcast/issues/571)).
- `transfer_playback` resumes at the currently playing track by passing its URI directly, instead of paginating through the whole context to find its position. Transferring playback of a large playlist is now a single request rather than dozens ([fondberg/spotcast#582](https://github.com/fondberg/spotcast/issues/582)).
- Starting playback on a device that Spotify Connect reports as momentarily unavailable now waits for it and retries once, instead of surfacing an immediate 404 popup. If the device stays unavailable, the error message is clear about the cause ([fondberg/spotcast#572](https://github.com/fondberg/spotcast/issues/572)).
- Spotify Connect devices keep a stable Home Assistant identity across reconnects. Entities and devices are now keyed on the device name and account rather than the ephemeral Spotify Connect device id, so a device that reconnects with a new id reuses its existing entity instead of spawning `_2`..`_6` duplicates ([fondberg/spotcast#580](https://github.com/fondberg/spotcast/issues/580), [fondberg/spotcast#586](https://github.com/fondberg/spotcast/issues/586)).
- `random` start on a Spotify editorial or algorithmic playlist now spans the whole playlist. The real track count is resolved through Spotify's internal metadata endpoint (which, unlike the public Web API, does not 404 on those playlists), falling back to the previous pseudo-random window only when that endpoint is unavailable ([fondberg/spotcast#569](https://github.com/fondberg/spotcast/issues/569)).

### Changes

- Desktop token authorization no longer requires the relay server. During setup you can now choose to authorize in the browser, copy the resulting address-bar URL, and paste it back into Home Assistant, which completes the token exchange itself. The relay server remains available as an optional automatic path.
- Reauthentication dialog strings are inlined (fixing a missing label in the reauth popup), and a mismatched French step key was corrected.

### Branding

- The integration now ships its own green Spotcast icon and logo through the local `brand/` folder, so it is no longer visually confused with the official Spotify integration.
- Package metadata capitalizes "Chromecast" and "Spotify Connect" correctly.

## v6.1.0 (2026-07-12)

### Changes

- Entity updates are now driven by a per-account `DataUpdateCoordinator`. Sensors, binary sensors and the Spotify Connect device manager refresh in a single API burst per update interval instead of polling individually, eliminating the "Updating spotcast sensor took longer than the scheduled update interval" log spam ([fondberg/spotcast#608](https://github.com/fondberg/spotcast/issues/608)).
- The `base_refresh_rate` option now controls the actual update cadence and applies immediately when changed, without the previous hidden 30 second polling floor ([fondberg/spotcast#592](https://github.com/fondberg/spotcast/issues/592)). Values as low as 5 seconds are accepted.
- Calling `homeassistant.update_entity` on a Spotcast entity now triggers a real refresh through the coordinator.
- Spotcast devices can now be deleted from the Home Assistant UI, and devices unavailable for more than 7 days are removed automatically. Spotify session devices (Jams) no longer accumulate forever ([fondberg/spotcast#608](https://github.com/fondberg/spotcast/issues/608)).
- Granted OAuth scopes are validated at setup: if a newer version requires additional permissions, Home Assistant now prompts for reauthentication instead of failing with unexplained 403 errors ([fondberg/spotcast#601](https://github.com/fondberg/spotcast/issues/601)).
- `play_media` accepts an album or playlist URI in `track_context`, playing the track inside that context (feature designed in [fondberg/spotcast#551](https://github.com/fondberg/spotcast/issues/551), thanks @sermayoral).
- `play_from_search` and search endpoints tolerate a null item list from Spotify (thanks @iammoen, [fondberg/spotcast#604](https://github.com/fondberg/spotcast/pull/604)); `random` start handles playlist payloads with an `items` key (thanks @superbullock, [fondberg/spotcast#609](https://github.com/fondberg/spotcast/pull/609)).

### Documentation

- The README and the configuration guide now state that part of the authentication uses the official Spotify desktop application's identity and may break without notice if Spotify changes its systems.
- One consolidated bug-report template (stable and pre-release), with links to the configuration and debug-log guides.

## v6.0.0 (2026-07-11)

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
