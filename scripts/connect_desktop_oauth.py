"""Script to connect to the spotify desktop oauth app and provide an
access and refresh token for the user
"""

from argparse import ArgumentParser, Namespace
from base64 import urlsafe_b64encode
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, HTTPServer
from os import urandom
from pathlib import Path
import sys
from threading import Thread
from urllib.parse import parse_qs, urlencode, urlparse
import webbrowser

from requests import HTTPError, post
from spotipy import Spotify

from custom_components.spotcast.const import SPOTIFY_CLIENT_ID

repo_root = Path(__file__).resolve().parent.parent

if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

SPOTIFY_SCOPES = [
    "streaming",
    "app-remote-control",
    "playlist-modify",
    "playlist-read",
    "user-modify",
    "user-modify-private",
    "user-personalized",
    "user-read-birthdate",
    "user-read-play-history",
    "user-read-playback-state",
    "user-read-email",
]


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code = None

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "code" in params:
            OAuthCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(
                b"<h1>Auth complete</h1>You can close this window."
            )
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def generatire_code_verifier() -> str:
    return urlsafe_b64encode(urandom(64)).rstrip(b"=").decode()


def generate_code_challenge(verifier: str) -> str:
    digest = sha256(verifier.encode()).digest()
    return urlsafe_b64encode(digest).rstrip(b"=").decode()


def get_token(token: str, redirect_uri: str, verifier: str) -> dict:
    token_data = {
        "client_id": SPOTIFY_CLIENT_ID,
        "grant_type": "authorization_code",
        "code": token,
        "redirect_uri": redirect_uri,
        "code_verifier": verifier,
    }

    response = post(
        "https://accounts.spotify.com/api/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=token_data,
        timeout=12,
    )

    try:
        response.raise_for_status()
    except HTTPError:
        print(response.text)

    data = response.json()

    print(f"Access Token  : {data['access_token']}")
    print(f"Refresh Token : {data['refresh_token']}")

    return data


def get_args() -> Namespace:
    """Provides the arguments from the terminal entry."""
    parser = ArgumentParser(description="Spotify OAuth PKCE Flow CLI")
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8080,
        help="Local por for redirect (default: 8080)",
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Interactive mode with clipboard output"
    )

    return parser.parse_args()


def main():
    """CLI entrypoint."""
    config = get_args()

    redirect_url = f"http://127.0.0.1:{config.port}/login"
    scope = " ".join(SPOTIFY_SCOPES)
    code_verifier = generatire_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    params = {
        "response_type": "code",
        "client_id": SPOTIFY_CLIENT_ID,
        "redirect_uri": redirect_url,
        "scope": scope,
        "code_challenge_method": "S256",
        "code_challenge": code_challenge,
    }

    auth_url = f"https://accounts.spotify.com/en/authorize?{urlencode(params)}"

    print("Lauching local HTTP server...")
    server = HTTPServer(("127.0.0.1", config.port), OAuthCallbackHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    print("Opening browser for Spotify authentication...")
    webbrowser.open(auth_url)

    while OAuthCallbackHandler.auth_code is None:
        pass

    code = OAuthCallbackHandler.auth_code

    print(f"Authorization code received: {code}")

    data = get_token(code, redirect_url, code_verifier)

    spotify = Spotify(auth=data["access_token"])

    print(spotify.devices())


if __name__ == '__main__':
    main()
