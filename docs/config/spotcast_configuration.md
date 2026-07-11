# Spotcast Configuration

This guide walks you through the setup of Spotcast in Home Assistant.

## 1. Create a Spotify Application

> [!TIP]
> If you configured the [Spotify](https://www.home-assistant.io/integrations/spotify/) integration in Home Assistant, this step is very likely already done and all you need is the Client ID and Client Secret of the application.
>
> You can set up a secondary application if you want, but this is not necessary.

In order to work with certain parts of the API, Spotcast requires access to the Spotify API through a personal Spotify Application. You can follow [these instructions](https://www.home-assistant.io/integrations/spotify/#create-a-spotify-application) from the official Spotify integration to create one. Keep note of your Client ID and Client Secret for future steps.

## 2. Start the relay server

In order to add the desktop application credentials from Spotify, we must redirect the connection information from your local computer to Home Assistant. This can be achieved by using a relay server on your local computer. This step is necessary because Spotify does not allow (for understandable security reasons) desktop credentials to be redirected to another location than the device making the connection. Please follow the instructions for your specific operating system:

### Windows

<details>
<summary>Windows Instructions</summary>

#### Option 1: PowerShell Server

<details>
<summary>PowerShell Server Instructions</summary>

> [!TIP]
> The PowerShell script does not require you to install any dependencies and can be run from a fresh Windows install.

Run the following PowerShell command:

```powershell
iwr https://raw.githubusercontent.com/Mincka/spotcast/main/scripts/relay_server.ps1 -UseBasicParsing | iex
```

> [!IMPORTANT]
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

> [!NOTE]
> This server setup requires you to have a recent Python interpreter on your computer. You can install Python with the installer provided by [python.org](https://www.python.org/downloads/). When given the option in the installation wizard, select `Add python to PATH`.

```powershell
curl.exe -sSL https://raw.githubusercontent.com/Mincka/spotcast/main/scripts/relay_server.py | python
```

> [!IMPORTANT]
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

> [!NOTE]
> This server setup requires you to have a recent Python interpreter on your computer. You can install Python with the installer provided by [python.org](https://www.python.org/downloads/) or by using the package manager of your distribution ([homebrew](https://brew.sh/) is available for MacOS).

#### One-Step setup instructions

```bash
curl -sSL https://raw.githubusercontent.com/Mincka/spotcast/main/scripts/relay_server.py | python
```

> [!IMPORTANT]
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

Once started, the relay server will show something like:

```text
Relay server running on http://127.0.0.1:8080/login
Redirecting to: https://my.home-assistant.io/redirect/oauth
Press CTRL+C to quit the server when done
```

If you see a similar message, you're ready for the next step.


## 3. Setup the Spotcast Integration in Home Assistant

Open Home Assistant and go to: `Settings -> Devices & Services -> + ADD INTEGRATION -> Spotcast` or use this direct link:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=spotcast)

Follow these instructions to finalize the setup in Home Assistant:

### 3.1 Application Credentials

> [!TIP]
> If you already made a Spotcast configuration in the past on this server, this step will not be required and you can skip to [3.2](#32-public-oauth-authorization).
>
> If your application credentials for your Spotify Application changed and you need to edit them, Home Assistant doesn't offer you that option when setting an integration with existing application credentials. You need to remove the current credentials manually, which can be done by following [these instructions](https://www.home-assistant.io/integrations/application_credentials/#deleting-application-credentials) from Home Assistant.

Once you see this window below in Home Assistant, provide a name (to your discretion) and provide the Client ID and Client Secret from your Spotify Application created in [Step 1](#1-create-a-spotify-application).

![Application Credential Step Screenshot](../../assets/images/docs/spotcast_configuration/3_1_application_credentials.png)

### 3.2 Public OAuth authorization

This step will authorize your account in your Spotify Application. A new window will appear asking you to link the account to Home Assistant. Ensure the `Your instance URL:` points to your current Home Assistant server and press the `Link account` button.

> [!TIP]
> Make sure the correct account is signed in. If Spotify doesn't ask you to log in, it is because a Spotify account is already signed in. If you are trying to set up an account for someone else in your household, make sure their account is the one signed into the browser.

### 3.3 Desktop Token authorization

A new window will open looking like this:

![Desktop Credential Approval](../../assets/images/docs/spotcast_configuration/3_3_desktop_token.png)

If the account under `Spotify for Desktop` is the account you are trying to set up, press the `Continue to the app` button, otherwise press `Not you?` and connect the proper account.

> [!CAUTION]
> If the relay server is not running at this point the setup will fail.

The same window as in step [3.2](#32-public-oauth-authorization) will appear. This is normal. This is to redirect your desktop credentials to Home Assistant. You can press the `Link Account` button.

### Done

At this point you should see your Spotify devices and account start to populate in the Home Assistant window.

> [!NOTE]
> You have completed the Spotcast setup at this point. You can close the relay server by pressing `CTRL+C` in your terminal. The relay server will only be required again for reauthenticating.

---

## Optional: Relay Server Configuration

Both relay servers (`relay_server.py` and `relay_server.ps1`) can be configured using CLI arguments to fit specific needs.

| Argument              | Description                                                                          | Default                                       |
| --------------------- | ------------------------------------------------------------------------------------ | --------------------------------------------- |
| `-r` `--redirect-url` | Redirects OAuth to your Home Assistant server (if not using `my.home-assistant.io`)  | `https://my.home-assistant.io/redirect/oauth` |

### Example: One-Step Install with Custom Redirect (Python)

```bash
curl -sSL https://raw.githubusercontent.com/Mincka/spotcast/main/scripts/relay_server.py | python - -r http://<your-home-assistant-server>
```

### Example: Manual Script with Custom Redirect (Python)

```bash
python relay_server.py -r http://<your-home-assistant-server>
```

### Example: Custom Redirect (PowerShell)

When piping the script with `iex`, set the `$redirectUrl` variable first; when running the downloaded file, use the `-r` argument:

```powershell
$redirectUrl = "http://<your-home-assistant-server>"
iwr https://raw.githubusercontent.com/Mincka/spotcast/main/scripts/relay_server.ps1 -UseBasicParsing | iex
```

```powershell
.\relay_server.ps1 -r http://<your-home-assistant-server>
```
