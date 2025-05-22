# Obtaining Desktop Credentials

> [!WARNING]
> This process is in alpha and is very likely
> 1. Unstable
> 2. Subject to change from the feedback of the testers.

Spotcast uses Spotify Desktop Application Oauthentication client to get the proper scope to enable chromecast registration when calling playback on a chromecast device. In order to get the credentials you will have to do the following (summary, detailed steps following):

1. Install required software
2. Clone the projecct
3. Install dependencies
4. Run the connection script
5. Profive the `access_token` and refresh_token `refresh_token` to Home Assistant

## Required software

In order to run the script, there are 2 softwares you must have installed on your local computer:

1. [Git](https://git-scm.com/downloads)
2. [Python 3.13+](https://www.python.org/downloads/)

If you are on Windows or Mac, I suggess you install from the websites directly. If you are on linux, follow your distribution package manager process to install both of them.

## Cloning the project

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

## Installing dependencies

The script relies on certain third party libraries. To install the dependencies run:

> [!NOTE]
> Depending on your installation, you might need to specify `pip3.13` instead of pip. If you get an error stating that `pip` is not a command, try calling the same command with `pip3.13` instead. This will apply to any command requesting to run `python`, replace with `python3.13`.

```shell
pip install -r requirements-scripts.txt
```

If you run into any error, your installation of python might not play well with installing packages in the main environement, if that is the case, a suggestion would be to build a virtual environement from the project and then run the script from that environement. To do so, do the following:



```shell
python -m venv .venv
```

Then you will have to activate the environement. The command to do so will changed based on the Operating system you are running and the shell. Run the command associatied with your OS and shell:

| OS | Shell | Command |
| :--- | :--- | :--- |
| Linux/Mac | bash/zsh | `source ./.venv/bin/activate` |
| Linux/Mac | fish | `source ./.venv/bin/activate.fish` |
| Linux/Mac | csh/tcsh | `source ./.venv/bin/activate.csh` |
| Linux/Mac | pwsh | `source ./.venv/bin/activate.ps1` |
| Windows | cmd | `.venv\Scripts\activate.bat` |
| Windows | PowerShell | `.venv\Scripts\activate.ps1` |

Then you can install dependencies with 

```shell
pip install -r requirements-scripts.txt
```

## Running the script

> [!NOTE]
> This is a good place to start the configuration process on Home Assistant if its not already in progress. Start configuring spotcast (see link below) until you get to a box asking for an Access and Refresh token.

Run the connection script by running

```shell
python scripts/connect_desktop_oauth.py
```

The script will open your browser:

1. Connect to spotify in the browser
2. When you see a page stating the connection was successful, you can close the tab
3. Copy and paste the `access_token` and `refresh_token` valuesin Home Assistant and press `OK`

> [!SUCCESS]
> You completed the desktop credential connection process
