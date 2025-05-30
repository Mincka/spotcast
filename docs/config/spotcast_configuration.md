# Spotcast Configuration

> [!WARNING]
> This process is in alpha and is very likely
> 1. Unstable
> 2. Subject to change from the feedback of the testers.

Spotcast uses Spotify Desktop Application OAuth authentication client to get the proper scope to enable Chromecast registration when calling playback on a Chromecast device. In order to get the credentials you will have to do the following (summary, detailed steps following):

1. Install required software
2. Run the relay server on your local computer
3. Setup the entry through Home Assistant

> [!WARNING]
> It is very important to run the instructions in the proper order. Do not start the Home Assistant configuration before completing the prior steps. Especially the [Relay Server](#run-the-relay-server-on-your-local-computer-relay-server) step.

## Install Required Software

In order to run the required relay server on your computer, you will need to install [Python 3.13+](https://www.python.org/downloads/).

If you are on Windows or Mac, I suggest you install from the websites directly. If you are on Linux, follow your distribution package manager process to install both of them.

## Run the relay server on your local computer

### One-Step Installation

For the next step, we will start a relay server on the local machine to redirect any Spotify OAuth redirects to Home Assistant.

Those who want to start the relay server quickly and conveniently may start the server with the following command:

> [!WARNING]
> If you are running `PowerShell` in Windows, Windows made the decision to create an alias for `curl` to `Invoke-WebRequest` which is **not** compatible with the `curl` utility. Because of this, you must call `curl.exe` instead of `curl` if running a `PowerShell` terminal. This issue does not affect `CMD`.

```shell
curl -sSL https://raw.githubusercontent.com/fondberg/spotcast/refs/heads/dev/scripts/relay_server.py | python
```

> [!IMPORTANT]
> Piping to `python` is controversial since you cannot read the code you are about to run. This is a reality that [Pi-hole raises](https://pi-hole.net/blog/2016/07/25/curling-and-piping-to-bash/#page-content) for their own project as well, just to give one example, even if they still provide a one-step install process (their documentation on the matter was also the inspiration of this section and info/warning). In the end, if you do not trust the source or the author of the source, don't run the code without vetting it first (this should also stand for a custom Home Assistant integration, it's still code and can do nasty things to your server and network if built with bad intent).
>
> If you would prefer to review the code before running the relay server, here are alternative methods. You can also review the code [here](https://github.com/fondberg/spotcast/blob/dev/scripts/relay_server.py).

#### Alternative 1: Clone and run

```shell
git clone https://github.com/fondberg/spotcast.git
cd spotcast
git checkout dev # required while we are still in alpha/beta
python scripts/relay_server.py
```
#### Alternative 2: Manual download and run

```shell
curl -o relay_server.py https://raw.githubusercontent.com/fondberg/spotcast/refs/heads/dev/scripts/relay_server.py
python relay_server.py
```

### Running the relay server

Once the server starts you should see the following in your terminal:

```
Relay server running on http://127.0.0.1:8080/login
Press CTRL+C to quit the server when done
```

If so, you are ready to set up the integration in Home Assistant.

## Setup the entry through Home Assistant

For the final step, all that remains to do is set up Spotcast directly in Home Assistant. You can do so by going into `Settings -> Devices & Services -> + ADD INTEGRATION -> Spotcast`, or click the following link:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=spotcast)

## Relay Server configuration

The relay server can be configured if needed to suit edge cases. The following arguments are available

| Argument             | Description                                                                                                                                         | Default                                       |
| :---:                | :---                                                                                                                                                | :---                                          |
| `-r` `--redirect-url` | Specify the URL where to redirect traffic. Can be used to specify your Home Assistant server directly if you do not have the `my` integration setup | `https://my.home-assistant.io/redirect/oauth` |

To specify configuration arguments, run any of the following based on your configuration method of choice

### One-Step Installation

```shell
curl -sSL https://raw.githubusercontent.com/fondberg/spotcast/refs/heads/dev/scripts/relay_server.py | python - -r http://<your-home-assistant-server>
```

### Running the script locally

```shell
python relay_server.py -r http://<your-home-assistant-server>
```

