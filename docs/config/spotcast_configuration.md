# Obtaining Desktop Credentials

> [!WARNING]
> This process is in alpha and is very likely
> 1. Unstable
> 2. Subject to change from the feedback of the testers.

Spotcast uses Spotify Desktop Application Oauth authentication client to get the proper scope to enable chromecast registration when calling playback on a chromecast device. In order to get the credentials you will have to do the following (summary, detailed steps following):

1. Install required software
3. Run the relay server on your local computer
4. Setup the entry through Home Assistant

> [!WARNING]
> It is very important to run the instruction in the proper order. Do not start the Home Assistant configuration before completing the prior steps. Especially the [Relay Server](#run-the-relay-server-on-your-local-computer-relay-server) step.

## Install Required Software

In order to run teh required relay server on your computer, you will need to install [Python 3.13+](https://www.python.org/downloads/).

If you are on Windows or Mac, I suggess you install from the websites directly. If you are on linux, follow your distribution package manager process to install both of them.

## Run the relay server on your local computer

### One-Step Installation

For the next step, we will start a relay server on the local machine to redirect any spotify oauth redirects to Home Assistant.


Those who want to start the relay server quick and conveniently may start the server with the following command:

```shell
curl -sSL https://raw.githubusercontent.com/fondberg/spotcast/refs/heads/dev/scripts/relay_server.py | python
```

> [!IMPORTANT]
> Piping to `python` is controversial since you cannot read the code you are about to run. This is a reality that [pihole raises](https://pi-hole.net/blog/2016/07/25/curling-and-piping-to-bash/#page-content) for there own project as well, just to give one example, even if they still provide a one-step install process (there documentation on the mather was also the inspiration of this section and info/warning). In the end, if you do not trust the source or the author of the source, don't run the code without vetting it first (this should also stand for a custom home assistant integration, its still code and can do nasty things to your server and network if built with bad intent).
>
> If you would prefer to review the code before running the relay server, here are alternative methods. You can also review the code [here](https://github.com/fondberg/spotcast/blob/dev/scripts/relay_server.py).

#### Alternative 1: Clone and run

```shell
git clone https://github.com/fondberg/spotcast.git
cd spotcast
git checkout dev # required while we are still in alpha/beta
python scripts/relay_server.py
```
#### Alternate 2: Manual download and run

```shell
curl -o relay_server.py https://raw.githubusercontent.com/fondberg/spotcast/refs/heads/dev/scripts/relay_server.py
python relay_server.py
```

### Running the relay server

Once the server start you should see the following in your terminal:

```
Relay server running on http://127.0.0.1:8080/login
Press CTRL+C to quit the server when done
```

If so, you are ready to setup the integration in Home Assistant.

## Setup the entry through Home Assistant

For the final step, all that remains to do is setup Spotcast directly in Home Assistant. You can do so by going into `Settings -> Devies & Services -> + ADD INTEGRATION -> Spotcast`, or click the following link:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=spotcast)
