"""A minimal relay server to send connection information to home assistant."""

from argparse import ArgumentParser, Namespace
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, urlencode

HOME_ASSISTANT_REDIRECT = "https://my.home-assistant.io/redirect/oauth"
LISTEN_PORT = 8080


class RedirectHandler(BaseHTTPRequestHandler):

    redirect_url = HOME_ASSISTANT_REDIRECT

    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path != "/login":
            self.send_error(404, "Not Found")
            return

        query = parse_qs(parsed_path.query)
        query_flat = {k: v[0] for k, v in query.items()}
        query_str = urlencode(query_flat)

        redirect_url = f"{self.redirect_url}?{query_str}"

        self.send_response(302)
        self.send_header("Location", redirect_url)
        self.end_headers()

        print(f"Redirected to: {redirect_url}")

    def log_message(self, format, *args):
        return  # Silence default logging


def get_args() -> Namespace:
    """Provides the arguments from stdin."""
    parser = ArgumentParser(
        prog="spotcast-relay-server",
        description="A Minimal OAuth relay for Home Assistant Spotcast",
    )

    parser.add_argument(
        "-r", "--redirect-url",
        default="https://my.home-assistant.io/redirect/oauth",
        help="Redirect base url (default: Home Assistant cloud redirect)",
        nargs='?',
    )

    # parser.add_argument(
    #     "-p", "--port",
    #     default=8080,
    #     type=int,
    #     help="Port to run the Relay server on (default: 8080)",
    #     nargs='?',
    # )

    return parser.parse_args()


def main():
    """Main loop of the relay server."""

    # parse arguments from standard in
    config = get_args()

    # setup the server
    RedirectHandler.redirect_url = config.redirect_url
    server_address = ("127.0.0.1", 8080)
    httpd = HTTPServer(server_address, RedirectHandler)

    print(f"Relay server running on http://127.0.0.1:{LISTEN_PORT}/login")
    print(f"Redirecting to: {config.redirect_url}")
    print("Press CTRL+C to quit the server when done")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nClosing relay server")


if __name__ == "__main__":
    main()
