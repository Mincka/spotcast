# Spotcast Configuration

This guide walks you through the setup of Spotcast in Home Assistant. The setup has two parts:

1. Create a Spotify Application (or reuse the one from the official Spotify integration).
2. Run the Spotcast config flow in Home Assistant.

During the config flow Spotcast performs two authorizations: a normal one for your Spotify account, and a second one under the identity of the official Spotify desktop application. For the second one you can simply **paste a URL** from your browser (no extra software), or optionally run a small **relay server** on your computer to automate the redirect.

> [!WARNING]
> Why the second authorization at all? Some Spotcast features require permissions that Spotify only grants to its own applications. Spotcast therefore authenticates one session under the identity of the official Spotify desktop application. Because this method is not officially supported by Spotify, it may stop working without notice if Spotify changes its authentication systems.

## Prerequisites

- A **Spotify Premium** account.
- Home Assistant `2026.4` or newer, with Spotcast [installed](../../README.md#installation).
- A web browser to complete the authorization.

## 1. Create a Spotify Application

> [!TIP]
> If you configured the [Spotify](https://www.home-assistant.io/integrations/spotify/) integration in Home Assistant, this step is very likely already done and all you need is the Client ID and Client Secret of the application.
>
> You can set up a secondary application if you want, but this is not necessary.

In order to work with certain parts of the API, Spotcast requires access to the Spotify API through a personal Spotify Application. You can follow [these instructions](https://www.home-assistant.io/integrations/spotify/#create-a-spotify-application) from the official Spotify integration to create one. In short:

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and create an app.
2. In the app settings, add `https://my.home-assistant.io/redirect/oauth` as a **Redirect URI**.
3. Keep note of your **Client ID** and **Client Secret** for step 2.

## 2. Setup the Spotcast Integration in Home Assistant

Open Home Assistant and go to: `Settings -> Devices & Services -> + ADD INTEGRATION -> Spotcast` or use this direct link:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=spotcast)

Follow these instructions to finalize the setup in Home Assistant:

### 2.1 Application Credentials

> [!TIP]
> If you already made a Spotcast configuration in the past on this server, this step will not be required and you can skip to [2.2](#22-public-oauth-authorization).
>
> If your application credentials for your Spotify Application changed and you need to edit them, Home Assistant doesn't offer you that option when setting an integration with existing application credentials. You need to remove the current credentials manually, which can be done by following [these instructions](https://www.home-assistant.io/integrations/application_credentials/#deleting-application-credentials) from Home Assistant.

Once you see this window below in Home Assistant, provide a name (to your discretion) and provide the Client ID and Client Secret from your Spotify Application created in [Step 1](#1-create-a-spotify-application).

![Application Credential Step Screenshot](../../assets/images/docs/spotcast_configuration/3_1_application_credentials.png)

### 2.2 Public OAuth authorization

This step will authorize your account in your Spotify Application. A new window will appear asking you to link the account to Home Assistant. Ensure the `Your instance URL:` points to your current Home Assistant server and press the `Link account` button.

> [!IMPORTANT]
> Make sure the correct account is signed in. If Spotify doesn't ask you to log in, it is because a Spotify account is already signed in. If you are trying to set up an account for someone else in your household, make sure their account is the one signed into the browser.

### 2.3 Desktop authorization

Spotcast now asks how you want to provide the second (desktop) authorization. Choose one of the two options.

#### Option A: Paste the redirect URL (recommended)

This option needs no extra software.

1. Select **Paste the redirect URL** in the menu.
2. Open the authorization link shown on the form and log in / authorize if asked.
3. Your browser will then try to open an address starting with `http://127.0.0.1:8080/login...` and show a **connection error**. This is expected, because nothing is listening on that address.
4. Copy the **full address** from your browser's address bar (it contains `?code=...&state=...`) and paste it into the form field, then submit.

Spotcast exchanges the authorization code and completes the setup.

> [!TIP]
> If you get an error that the code could not be exchanged, open the authorization link again to get a fresh code. Authorization codes are single-use.

#### Option B: Use the relay server (automatic)

If you prefer the browser to be redirected back to Home Assistant automatically, run the [relay server](#optional-relay-server) on the same computer as your browser first, then select **Use the relay server** in the menu and complete the authorization. See [the appendix](#optional-relay-server) for how to start it.

### Done

At this point you should see your Spotify devices and account start to populate in the Home Assistant window.

> [!NOTE]
> You have completed the Spotcast setup. The same desktop authorization step is required again if you ever need to reauthenticate.

---

## Integration Options

Each account has its own options, available under **Settings > Devices & services > Spotcast >** (your account) **> Configure**. Changes apply immediately, without a restart.

### Set as default account

Marks the account as the default Spotcast account, used by actions and WebSocket endpoints when no account is specified. Setting it on one account clears it on the others.

### Base Refresh Rate

How often (in seconds) Spotcast refreshes the account data from Spotify: profile, available devices, playback state and library counts. Defaults to `30`, minimum `5`. Raise it if you want fewer calls to the Spotify API; lower it if you want playback state to react faster.

### Days before removing unavailable devices

A Spotify Connect device that disappears from the account (a phone that left the network, an ended [Jam](https://support.spotify.com/us/article/jam/) session) keeps its `media_player` entity for this many days before Spotcast removes the entity and its device registry entry. Defaults to `7`. Set it to `0` to remove devices as soon as they become unavailable.

The countdown survives Home Assistant restarts, and also applies to leftover devices created by previous Spotcast versions: they start aging as soon as the integration loads and are cleaned up once past the timeout.

### Device filter mode and patterns

Controls which Spotify Connect devices get a `media_player` entity. Patterns are case-insensitive, comma-separated, and support `*` wildcards:

- **deny** (default): devices whose name matches any pattern are ignored. With no patterns, every device is kept. Example: `*Jam*, Pixel 7 Pro` hides Jam sessions and a specific phone.
- **allow**: only devices whose name matches a pattern get an entity. Example: `Kitchen*, Living Room TV`. With no patterns, the filter is ignored (so a misconfiguration cannot hide every device).

Filtered devices can still be used as cast targets by name in action calls; the filter only controls entity creation. A device filtered after its entity already existed becomes unavailable and is removed by the stale-device timeout above.

#### Example: a household that uses Jam sessions a lot

Every Jam session and every guest phone shows up as a Spotify Connect device and would get its own `media_player` entity. To keep only the fixed speakers:

- **Deny mode** (keep everything except known noise):
  - Device filter mode: `deny`
  - Device filter patterns: `*Jam*, Pixel 7 Pro, iPhone*`
  - Result: Jams and the listed phones never get entities; any new speaker still appears automatically.
- **Allow mode** (only ever these devices):
  - Device filter mode: `allow`
  - Device filter patterns: `Kitchen*, Living Room TV, JULIEN-PC`
  - Result: only devices matching those names get entities; everything else (Jams, guests, new phones) is ignored. New devices you buy must be added to the list before they appear.

Pair either mode with a short **Days before removing unavailable devices** (for example `1`) so entities from devices that stop matching, or that existed before you configured the filter, disappear quickly.

> [!TIP]
> The pattern matches the **Spotify Connect device name** (what you see in the Spotify app's device picker), not the Home Assistant entity id.

#### Finding a device's name (especially in allow mode)

In allow mode a new device gets no entity until you add its name, so you need a way to see the names of devices the filter is hiding. The filter only controls entity creation: the **Spotify Devices** sensor still lists every device Spotify reports, filtered or not. While the device is online (playing or recently active in the Spotify app):

1. Open **Developer Tools > States** and look at `sensor.spotcast_<account>_spotify_devices`.
2. Its `devices` attribute lists every Spotify Connect device with its exact `name`; copy the name (or a wildcard version of it) into your patterns.

Alternatively, the name is exactly what the Spotify app shows in its device picker ("Listening on ..."), so you can read it from there too.

---

## Optional: Relay Server

Instead of pasting the redirect URL manually (Option A above), you can run a small relay server on your computer that redirects the desktop authorization back to Home Assistant automatically (Option B). This is entirely optional.

> [!IMPORTANT]
> Run the relay server on the **same computer** where you complete the setup in your web browser, and keep it running until the setup is done. It is only needed during setup (and later for reauthentication).

Please follow the instructions for your specific operating system:

### Windows

<details>
<summary>Windows Instructions</summary>

#### Option 1: PowerShell Server

<details>
<summary>PowerShell Server Instructions</summary>

> 💡 **Tip**
>
> The PowerShell script does not require you to install any dependencies and can be run from a fresh Windows install.

Run the following PowerShell command:

```powershell
iwr https://raw.githubusercontent.com/Mincka/spotcast/main/scripts/relay_server.ps1 -UseBasicParsing | iex
```

> ⚠️ **Caution**
>
> Piping any script from the internet is potentially unsafe. If you don't trust the source, review the code before running it. The script is part of this repository and can be reviewed [here](https://github.com/Mincka/spotcast/blob/main/scripts/relay_server.ps1).

##### Alternative: Manual Download and Run

This method allows you to save the file to your computer, to be able to review the code yourself before running it:

```powershell
iwr https://raw.githubusercontent.com/Mincka/spotcast/main/scripts/relay_server.ps1 -OutFile relay_server.ps1
.\relay_server.ps1
```

</details>

#### Option 2: Python Server

<details>
<summary>Python Server Instructions</summary>

If you prefer to use Python directly, you can run this one-step configuration:

> ℹ️ **Note**
>
> This server setup requires you to have a recent Python interpreter on your computer. You can install Python with the installer provided by [python.org](https://www.python.org/downloads/). When given the option in the installation wizard, select `Add python to PATH`.

```powershell
curl.exe -sSL https://raw.githubusercontent.com/Mincka/spotcast/main/scripts/relay_server.py | python
```

> ⚠️ **Caution**
>
> Piping any script from the internet is potentially unsafe. If you don't trust the source, review the code before running it. You can review the relay server script [here](https://github.com/Mincka/spotcast/blob/main/scripts/relay_server.py). Alternative methods that download the script to your machine before running are also provided.

##### Alternative 1: Clone the repository and Run

This method requires [git](https://git-scm.com/downloads) to be installed on your computer:

```powershell
git clone https://github.com/Mincka/spotcast.git
cd spotcast
python scripts/relay_server.py
```

##### Alternative 2: Manual Download and Run

This method allows you to save the file to your computer, to be able to review the code yourself before running it:

```powershell
curl.exe -o relay_server.py https://raw.githubusercontent.com/Mincka/spotcast/main/scripts/relay_server.py
python relay_server.py
```

</details>
</details>

### Mac OS/Linux

<details>
<summary>Mac OS/Linux Instructions</summary>

> ℹ️ **Note**
>
> This server setup requires you to have a recent Python interpreter on your computer. You can install Python with the installer provided by [python.org](https://www.python.org/downloads/) or by using the package manager of your distribution ([homebrew](https://brew.sh/) is available for MacOS).

#### One-Step setup instructions

```bash
curl -sSL https://raw.githubusercontent.com/Mincka/spotcast/main/scripts/relay_server.py | python
```

> ⚠️ **Caution**
>
> Piping any script from the internet is potentially unsafe. If you don't trust the source, review the code before running it. You can review the relay server script [here](https://github.com/Mincka/spotcast/blob/main/scripts/relay_server.py). Alternative methods that download the script to your machine before running are also provided.

##### Alternative 1: Clone the repository and Run

This method requires [git](https://git-scm.com/downloads) to be installed on your computer:

```bash
git clone https://github.com/Mincka/spotcast.git
cd spotcast
python scripts/relay_server.py
```

##### Alternative 2: Manual Download and Run

This method allows you to save the file to your computer, to be able to review the code yourself before running it:

```bash
curl -o relay_server.py https://raw.githubusercontent.com/Mincka/spotcast/main/scripts/relay_server.py
python relay_server.py
```

</details>

### Validation

Once started, the relay server confirms it is listening. The Python server shows:

```text
Relay server running on http://127.0.0.1:8080/login
Redirecting to: https://my.home-assistant.io/redirect/oauth
Press CTRL+C to quit the server when done
```

The PowerShell server shows:

```text
Relay server running at http://127.0.0.1:8080/login
Target redirect URL: https://my.home-assistant.io/redirect/oauth
Open the Spotcast integration setup in Home Assistant.
(Press Ctrl+C to cancel.)
```

If you see a similar message, you're ready to select **Use the relay server** in the config flow.

> [!TIP]
> If the server fails to start because port `8080` is already in use, stop the application using that port and start the relay server again.

### Relay Server Configuration

Both relay servers (`relay_server.py` and `relay_server.ps1`) can be configured using CLI arguments to fit specific needs.

| Argument              | Description                                                                          | Default                                       |
| --------------------- | ------------------------------------------------------------------------------------ | --------------------------------------------- |
| `-r` `--redirect-url` | Redirects OAuth to your Home Assistant server (if not using `my.home-assistant.io`)  | `https://my.home-assistant.io/redirect/oauth` |

#### Example: One-Step Install with Custom Redirect (Python)

```bash
curl -sSL https://raw.githubusercontent.com/Mincka/spotcast/main/scripts/relay_server.py | python - -r http://<your-home-assistant-server>
```

#### Example: Manual Script with Custom Redirect (Python)

```bash
python relay_server.py -r http://<your-home-assistant-server>
```

#### Example: Custom Redirect (PowerShell)

When piping the script with `iex`, set the `$redirectUrl` variable first; when running the downloaded file, use the `-r` argument:

```powershell
$redirectUrl = "http://<your-home-assistant-server>"
iwr https://raw.githubusercontent.com/Mincka/spotcast/main/scripts/relay_server.ps1 -UseBasicParsing | iex
```

```powershell
.\relay_server.ps1 -r http://<your-home-assistant-server>
```
