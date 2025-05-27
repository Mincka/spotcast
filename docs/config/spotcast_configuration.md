# Obtaining Desktop Credentials

> [!WARNING]
> This process is in alpha and is very likely
> 1. Unstable
> 2. Subject to change from the feedback of the testers.

Spotcast uses Spotify Desktop Application Oauth authentication client to get the proper scope to enable chromecast registration when calling playback on a chromecast device. In order to get the credentials you will have to do the following (summary, detailed steps following):

1. Install required software
2. Clone the projecct
3. Run the relay server on your local computer
4. Setup the entry through Home Assistant

> [!WARNING]
> It is very important to run the instruction in the proper order. Do not start the Home Assistant configuration before completing the prior steps. Especially the [Relay Server](#run-the-relay-server-on-your-local-computer-relay-server) step.

## Install Requied Software

In order to run the script, there are 2 softwares you must have installed on your local computer:

1. [Git](https://git-scm.com/downloads)
2. [Python 3.13+](https://www.python.org/downloads/)

If you are on Windows or Mac, I suggess you install from the websites directly. If you are on linux, follow your distribution package manager process to install both of them.

## Clone the project

In order to have the script on your machine, please run the following (I suggest you run one command at a time in case of errors):

```shell
git clone https://github/fondberg/spotcast
cd spotcast
git checkout dev
```

### fatal: destination path

If you get an error `fatal: destination path 'spotcast' already exists and is not an empty directory.`, this means you already cloned the project in the past. Instead, run the following:

```shell
cd spotcast
git fetch
git pull
```
## Run the relay server on your local computer

For the next step, we will start a relay server on the local machine to redirect any spotify oauth redirects to Home Assistant. From the spotcast project directory run the following:

```python
python scripts/relay_server.py
```

You should see the following in your terminal

```
Relay server running on http://127.0.0.1:8080/login
Press CTRL+C to quit the server when done
```

If so, you are ready to setup the integration in Home Assistant.

## Setup the entry through Home Assistant

For the final step, all that remains to do is setup Spotcast directly in Home Assistant. You can do so by going into `Settings -> Devies & Services -> + ADD INTEGRATION -> Spotcast`, or click the following link:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=spotcast)
