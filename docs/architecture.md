# Spotcast Architecture

This document explains how Spotcast is built: how it authenticates to
Spotify, what each token is for, how it drives Chromecast devices, how it
relates to the built-in Home Assistant Spotify integration, and how data
flows from Spotify into Home Assistant entities, actions, and the
WebSocket API.

It is a technical reference for contributors. For setup instructions, see
the [configuration guide](./config/spotcast_configuration.md).

---

## 1. What Spotcast is

Spotcast is a Home Assistant **custom integration** (`integration_type:
service`, `iot_class: cloud_polling`). Its job is to start and transfer
Spotify playback from Home Assistant automations, including onto devices
that are not themselves signed into a Spotify account (Chromecast
speakers). It deliberately keeps read-only "Spotify information" features
minimal and leaves comprehensive control to SpotifyPlus.

A single Home Assistant install can hold several Spotcast accounts, each
its own config entry, with one marked as the default for action calls.

---

## 2. High-level structure

```
Config entry (per Spotify account)
  data.external_api   -> public OAuth token   (Web API)
  data.desktop_api    -> desktop OAuth token   (elevated capabilities)
        |
        v
  SpotifyAccount  (spotify/account.py)
    sessions["public"]  = PublicSession   -> api.spotify.com  (spotipy)
    sessions["private"] = DesktopSession  -> accounts.spotify.com + spclient
        |
        +--> SpotcastCoordinator  (one burst poll per interval)
        |        -> Sensors / Binary sensors / Media players
        |
        +--> ServiceHandler  (the spotcast.* actions)
        |
        +--> WebSocket API   (spotcast/* commands for frontend cards)
        |
        +--> SpotifyController (Chromecast authentication handshake)
```

The `SpotifyAccount` is the center of the integration. It owns the two
Spotify sessions, exposes typed helpers over the Web API, caches results
in per-topic datasets, and hands its data to everything else.

---

## 3. The two Spotify identities

Spotcast authenticates each account **twice**, under two different
Spotify OAuth applications, because some capabilities Spotify only grants
to its own first-party desktop application. Both tokens belong to the same
Spotify user; they differ only in which application requested them and
therefore which permissions they carry.

Spotcast did not always work this way. For how the two-token design came
to be, and the Spotify API changes that forced it, see the history in
section 13.

The account keeps them under a stable naming scheme
(`SpotifyAccount.SESSION_CONFIG_MAP`):

| Session key | Config entry key | Class | Purpose |
| --- | --- | --- | --- |
| `public` | `external_api` | `PublicSession` | Standard Spotify Web API |
| `private` | `desktop_api` | `DesktopSession` | Capabilities reserved to the desktop app |

### 3.1 Public session (`external_api`)

- Class: `PublicSession` (`sessions/public_session.py`), base
  `ConnectionSession`. API base `https://api.spotify.com`.
- It does **not** hardcode a client id. It authenticates through a Home
  Assistant `AbstractOAuth2Implementation`, resolved from
  `config_entry.data["external_api"]["auth_implementation"]`. The client
  id therefore comes from the user's **Application Credentials** (the same
  Spotify app the built-in Spotify integration uses; see section 6).
- Scopes are the eleven listed in `SpotifyAccount.SCOPE`
  (`user-modify-playback-state`, `user-read-playback-state`,
  `user-read-private`, `playlist-read-private`,
  `playlist-read-collaborative`, `user-library-read`,
  `user-library-modify`, `user-top-read`, `user-read-playback-position`,
  `user-read-recently-played`, `user-follow-read`).
- Refresh uses Home Assistant's standard OAuth2 refresh
  (`implementation.async_refresh_token`).
- This session backs every ordinary Web API call, made through the
  `spotipy` client held at `account.apis["public"]`.

### 3.2 Desktop session (`desktop_api`)

- Class: `DesktopSession` (`sessions/desktop_session.py`), base
  `ConnectionSession`.
- Client id is fixed: `SPOTIFY_CLIENT_ID =
  "65b708073fc0480ea92a077233ca87bd"` (`const.py`), the id of Spotify's
  own desktop application. This is what grants the elevated capabilities.
- The initial token is obtained during the config flow through a PKCE
  implementation, `RelayedOAuth2ImplementationWithPcke`
  (`sessions/oauth_pcke_implementation.py`), which requests a different,
  more privileged scope set: `streaming`, `app-remote-control`,
  `playlist-modify`, `playlist-read`, `user-modify`, `user-modify-private`,
  `user-personalized`, `user-read-birthdate`, `user-read-play-history`,
  `user-read-playback-state`, `user-read-email`. Its redirect URI is the
  fixed local address `http://127.0.0.1:8080/login`.
- Runtime refresh does **not** go through Home Assistant OAuth. It is a
  raw `POST https://accounts.spotify.com/api/token` with body
  `{grant_type: refresh_token, client_id: SPOTIFY_CLIENT_ID,
  refresh_token: ...}`.
- Because it impersonates the desktop application, this method is
  unofficial and can break if Spotify changes its systems.

### 3.3 How the two tokens work together

- Both must resolve to the **same Spotify account**. The config flow
  verifies this: after both authorizations it compares the profile id of
  each and aborts on a mismatch (`public_private_accounts_mismatch`).
- At setup, only the **public** token's profile is fetched (the desktop
  token is blocked on `api.spotify.com`; see section 4.3). The desktop
  token is validated but not exercised against the Web API.
- The public token does the day-to-day Web API work. The desktop token is
  used only where the public one is not allowed (section 4).

### 3.4 Token storage, validity, and rotation

Tokens live inside the config entry (`external_api` / `desktop_api`), and
the sessions layer manages their lifetime:

- `ConnectionSession` holds an in-memory copy of the entry data. A token
  is considered valid while `expires_at - 600s > now` (a ten-minute
  safety offset).
- `async_ensure_token_valid` refreshes a token when it is close to
  expiry, under a per-session lock, and returns whether a refresh
  happened.
- Crucially, the desktop refresh token is **single-use**: Spotify returns
  a brand-new `refresh_token` on every refresh and revokes the old one. A
  session only updates its in-memory copy, so the account is responsible
  for persisting the rotation. `SpotifyAccount.async_ensure_tokens_valid`
  reads the live entry, copies each session's refreshed token (including
  the rotated desktop refresh token) into a fresh data dict, and writes it
  back with `hass.config_entries.async_update_entry`. Without this
  write-back a restart would present a revoked refresh token and force a
  reauthentication.

### 3.5 Resilience: the retry supervisor

Every refresh is guarded by a `RetrySupervisor` (a small circuit
breaker). On a network or upstream error it marks the session unhealthy
and sets a 30-second backoff before another refresh is attempted; during
that window callers get a clear `UpstreamServerNotready` instead of
hammering Spotify. It logs the first failure at ERROR and subsequent ones
at DEBUG to avoid log spam.

---

## 4. What the desktop token is used for

The desktop token exists for exactly three reasons. Everything else uses
the public token.

### 4.1 Authenticating Chromecast devices (the original reason)

The desktop token is what lets a Chromecast speaker log into Spotify as
the user. This is covered in detail in section 5.

### 4.2 Resolving editorial playlists via the internal endpoint

Spotify's public Web API returns `404` for its own
editorial/algorithmic playlists (the `37i9...` ones). The desktop token
can read them through an unofficial internal endpoint:

```
GET https://spclient.wg.spotify.com/playlist/v2/playlist/{id}/metadata
Authorization: Bearer <desktop token>
Accept: application/json
```

This returns a JSON document including `length` and
`attributes.name`/`attributes.description` even for editorial playlists.
Spotcast uses it in `spotify/internal_api.py` for two features:

- **Real random-start** (`async_get_playlist_length`): picking a random
  start index across the *whole* editorial playlist instead of guessing
  within the first few tracks.
- **Current playlist sensor** (`async_get_playlist_name`): resolving the
  human-readable name of whatever playlist is currently playing, so it
  works for editorial contexts too.

Both are wrapped so that any failure returns `None` and the caller falls
back to supported behaviour. The endpoint lives on `spclient`, which is
not subject to the aggressive rate limiting described next.

### 4.3 Where the desktop token must never go

The desktop token is blocked on `api.spotify.com`: the first call returns
`429 rate limit exceeded`, a permanent block disguised as a rate limit
(the `Retry-After` window resets but requests keep failing). Spotify
started returning these in December 2025 (see section 13). Every
desktop-token feature therefore uses `spclient`/device endpoints, **never
`api.spotify.com`**, and degrades gracefully. Reading arbitrary player
state (smart shuffle, live context) would require a persistent connection
to Spotify's dealer WebSocket to obtain a connection id; that is not built
and those features are intentionally deferred.

---

## 5. Chromecast playback

Spotcast can start playback on a Chromecast that is not signed into
Spotify. It does this by authenticating the cast device against the user's
account with the desktop token, then transferring playback to it over the
normal Web API.

### 5.1 Discovery: reuse of the built-in cast integration

Spotcast does **not** run its own zeroconf discovery. It lists cast
devices from Home Assistant's built-in `cast` integration
(`async_entities_from_integration(hass, "cast", ["media_player"])`) and
builds a `pychromecast.Chromecast` object from each `CastDevice`'s cast
info plus Home Assistant's shared zeroconf instance. `pychromecast` itself
is provided by that `cast` dependency, not by Spotcast's own requirements.

### 5.2 The authentication handshake

`SpotifyController` (`chromecast/spotify_controller.py`) is a
`pychromecast` `BaseController` bound to the Spotify cast application
(`APP_ID = "CC32E753"`, namespace
`urn:x-cast:com.spotify.chromecast.secure.v1`). It is attached to the cast
device with `register_handler`. The flow:

1. Launch the Spotify app on the device and send a `getInfo` message
   carrying the device's `remoteName`/`deviceID`.
2. The device replies `getInfoResponse`. The handler takes the
   **desktop** token (`account.get_token("private")`) and
   `POST`s to `https://spclient.wg.spotify.com/device-auth/v1/refresh`
   with the device's `clientID`/`deviceID`, minting a per-device
   `accessToken` blob (12-second timeout).
3. The controller sends that blob to the device in an `addUser` message.
4. `addUserResponse` signals success; the device is now signed in as the
   user and appears in the account's Spotify Connect device list.

Waiting is bounded: up to ~10 one-second polls for the app to report
ready, then an `AppLaunchError` if it never does.

### 5.3 Turning the handshake into playback

Once the cast device is authenticated it is an ordinary Spotify Connect
target. Spotcast identifies it by a deterministic id, `md5(device_name)`,
which is the same `deviceID` used in the handshake, and then transfers
playback to it through the public Web API
(`account.async_play_media(device_id, uri, ...)`). The controller only
performs authentication; it never carries the track transfer.

---

## 6. Relationship to the built-in Home Assistant Spotify integration

Spotcast is independent from Home Assistant's official `spotify`
integration but deliberately builds on parts of it. The `manifest.json`
declares `dependencies: ["spotify", "cast", "application_credentials"]`,
so Home Assistant loads all three before Spotcast.

- **Application Credentials / OAuth server.** Spotcast's
  `application_credentials.py` re-exports `async_get_authorization_server`
  straight from `homeassistant.components.spotify.application_credentials`.
  In other words, Spotcast reuses the official integration's definition of
  Spotify's OAuth endpoints, and the Spotify **app** (client id/secret) a
  user registered for the official integration is reused for Spotcast's
  public session. If you already set up the official Spotify integration,
  its credentials satisfy Spotcast's public authorization.
- **The `spotify` dependency** also brings the `spotifyaio` library into
  the environment (Spotcast's own Web API client is `spotipy`; the test
  suite references `spotifyaio` because the dependency provides it, so it
  is not a direct runtime requirement in the manifest).
- **The `cast` dependency** provides device discovery and `pychromecast`
  (section 5.1).
- **`application_credentials`** is the Home Assistant subsystem for
  storing OAuth client credentials.

What Spotcast does **not** do: it does not replace or wrap the official
integration's `media_player`, and it does not read the official
integration's config entry. It is a separate account with its own config
entry, its own tokens, its own entities, and its own actions. The two can
coexist; they simply share the underlying Spotify application credentials.

---

## 7. Data flow and caching

All entity updates are driven by a single per-account
`SpotcastCoordinator` (`coordinator.py`) rather than per-entity polling.
Each interval it refreshes profile, devices, playback state, playlist and
liked-song counts, and the current playlist name in one burst, and returns
one data dict consumed by every entity.

The account caches each topic in a `Dataset` with its own time-to-live,
derived from `base_refresh_rate` (default 30s) times a per-dataset factor.
Playback state refreshes twice as often as the base rate; profile and
categories far less often. `base_refresh_rate` is an option and applies
immediately when changed, adjusting the coordinator interval without a
reload.

The current-playlist name is resolved from the playback context uri (from
the public playback state) through the internal endpoint (section 4.2),
and cached per context uri so it is only looked up when the context
changes.

---

## 8. Entities

Per account, Spotcast creates:

- **Sensors** (`sensor/`): devices count, profile, playlists count, liked
  songs count, product, followers, account type, and current playlist.
- **Binary sensors** (`binary_sensor/`): is-default, and a profile
  malfunction indicator.
- **Media players** (`media_player/`): one per Spotify Connect device the
  account can see. Device identity is keyed on a stable slug of the device
  name plus the account id, so a device that reconnects with a new Spotify
  Connect id reuses its existing entity instead of spawning duplicates.

---

## 9. Actions (services)

The action layer is a thin dispatcher. `ServiceHandler`
(`services/service_handler.py`) is registered for every action in
`services/const.py::SERVICE_SCHEMAS` and routes each call to its handler.
The current actions are: `play_media`, `play_dj`, `play_liked_songs`,
`transfer_playback`, `play_custom_context`, `play_from_search`,
`add_to_queue`, `play_saved_episodes`, and `like_media`.

Each action optionally takes an `account` id and falls back to the default
account otherwise, resolves the target media player, and calls the
corresponding `SpotifyAccount` helper. Playback actions accept a `data`
object of extra modifiers (position/offset, shuffle, repeat, volume, and
similar) applied through `async_apply_extras`.

---

## 10. WebSocket API

Spotcast registers a set of Home Assistant WebSocket commands
(`websocket/`) for use by frontend cards: `accounts`, `devices`,
`cast_devices`, `categories`, `playlists`, `tracks`, `liked_media`,
`search`, `view`, and `player`. These are read-oriented endpoints backed
by the same account datasets, letting a custom dashboard query the account
without going through entities.

---

## 11. Dependencies

| Dependency | Type | Why |
| --- | --- | --- |
| `spotify` (HA integration) | manifest dependency | OAuth authorization server + Application Credentials reuse; brings `spotifyaio` |
| `cast` (HA integration) | manifest dependency | Chromecast discovery + `pychromecast` |
| `application_credentials` (HA) | manifest dependency | Stores the Spotify OAuth client credentials |
| `spotipy>=2.26.0` | Python requirement | Spotcast's Spotify Web API client |
| `RapidFuzz>=3.14.5` | Python requirement | Fuzzy matching for `play_from_search` |

Loggers surfaced in diagnostics: `spotipy`, `pychromecast`.

---

## 12. Failure modes and graceful degradation

- **Missing scopes.** OAuth scopes are frozen at consent time. If a new
  release adds a required scope, `get_missing_scopes` detects it against
  the stored public token and raises a reauthentication request rather
  than failing with opaque 403s.
- **Unofficial endpoints.** Every desktop-token internal call returns
  `None` on any error, and callers fall back (real random-start reverts to
  a pseudo-random window; the current-playlist sensor reports inactive).
- **Editorial 404s.** Public Web API 404s on editorial playlists are
  handled gracefully instead of surfacing errors.
- **Upstream instability.** The retry supervisor backs off on refresh
  failures and reports `UpstreamServerNotready` instead of retry storms.
- **Playback to an unavailable device.** Starting playback on a device
  Spotify reports as momentarily unavailable waits and retries once before
  surfacing a clear error.

---

## 13. How the two-token design came to be

Spotcast did not originally need a desktop token. This section explains
what changed on Spotify's side and why the current design exists.

### The original approach: web-player cookies

Before v6, Spotcast authenticated with two browser cookies, `sp_dc` and
`sp_key`, copied from a signed-in `open.spotify.com` session. It exchanged
the `sp_dc` cookie at `open.spotify.com/get_access_token` for a **Web
Player access token**. That token carried the Web Player's own elevated
capabilities (starting playback, transferring it to any device,
controlling the Spotify Connect graph) without the user ever registering a
Spotify application. No OAuth, no desktop token: the cookie borrowed the
web player's first-party identity.

This mattered because those capabilities, notably the `streaming` and
`app-remote-control` scopes and full Connect control, are effectively
reserved to Spotify's own first-party clients. A regular third-party OAuth
application is not granted them. The web-player cookie sidestepped that by
inheriting the web player's identity.

### What Spotify changed

Spotify progressively closed that path:

- **`sp_key` cookie removed (2023-2024).** Spotify stopped issuing the
  `sp_key` cookie on `open.spotify.com` (fondberg/spotcast #309, #350).
  Cookie auth limped on with `sp_dc` alone.
- **Web API deprecation wave (27 November 2024).** Spotify
  [removed a large set of endpoints for third-party apps](https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api):
  audio-features, audio-analysis, recommendations, related-artists,
  featured-playlists, category playlists, and the `/views/` browse hubs.
  This is what removed Spotcast's audio-feature, category-playlist and
  `views` features across v6.
- **TOTP / server-time requirement on `get_access_token` (spring 2025).**
  Spotify began requiring a time-based one-time password, computed against
  its `/server-time`, on the web-player token endpoint. Tools built on
  `sp_dc` broke with `Invalid TOTP` / `ServerTime` errors
  (fondberg/spotcast #543, 7 May 2025, plus the "current outage" notices
  in the repository around that time). Keeping up meant reverse-engineering
  and chasing a rotating TOTP secret.
- **Web-player token path effectively closed (mid 2025).** The
  `get_access_token` route became unusable for third-party use (the same
  break hit librespot and every `sp_dc`-based tool). At that point cookie
  authentication was no longer viable at all.

Dates outside the 27 November 2024 change (a published Spotify
announcement) are approximate, anchored to the reports in the project's
own issue tracker.

### The v6 answer: two OAuth tokens

Rather than keep fighting the cookie/TOTP arms race, v6 rebuilt
authentication on OAuth and split it in two (sections 3.1 and 3.2):

- A **public token** from the user's own Spotify application (through Home
  Assistant Application Credentials) for ordinary Web API calls. Fully
  supported and stable, but, being a third-party app, it lacks the
  elevated capabilities.
- A **desktop token**, obtained by authorizing under Spotify's official
  desktop application client id (`65b708073fc0480ea92a077233ca87bd`)
  through a PKCE flow. Authorizing as the desktop app recovers the
  first-party capabilities the web-player cookie used to provide:
  `streaming`, `app-remote-control`, and the device authentication that
  lets a Chromecast sign in (section 5).

### The desktop token blocked on the Web API (December 2025)

Initially v6 still used the desktop token for some `api.spotify.com`
calls. Around **22-23 December 2025** Spotify began returning **fake `429`
responses** for the desktop client id on every `api.spotify.com` endpoint,
permanent blocks disguised as rate limits (the `Retry-After` window resets
but the calls keep failing). The desktop token kept working on
`spclient.wg.spotify.com`, and the public OAuth token was unaffected on
`api.spotify.com` (fondberg/spotcast #593, fixed in
[fondberg/spotcast#598](https://github.com/fondberg/spotcast/pull/598)).

This is what fixed the two tokens into their current division of labour:

- **all `api.spotify.com` calls go through the public token** (the private
  Spotify client is no longer used for the Web API);
- **the desktop token is used only on `spclient`** (Chromecast device
  authentication, section 5, and the internal editorial-playlist endpoint,
  section 4.2).

The same change stopped validating the desktop token against the Web API
during setup, added the `user-library-modify` scope to the public token
(for `like_media`), and made the deprecated `audio-features` lookup and
the non-critical extras (shuffle/repeat/volume) degrade gracefully instead
of failing a playback transfer. So while the two-token *design* dates to
the v6 rewrite, the strict rule in section 4.3 ("never send the desktop
token to `api.spotify.com`") dates specifically to this December 2025
block.

The through-line is unchanged: Spotcast has always needed
**first-party-level capabilities** to do its job. Originally it inherited
them for free from a web-player cookie token; once Spotify locked that
down, v6 had to obtain equivalent capabilities the only remaining way, by
authorizing under the desktop application's identity. The desktop token is
the successor to the old cookie trick, not a new requirement invented for
its own sake.

This also explains the reauthentication-on-new-scope behaviour
(section 12): because scopes are frozen at consent time and the two tokens
carry different scope sets, adding a capability can require re-consent.
