"""A minimal relay server to send connection information to home assistant."""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, urlencode

HOME_ASSISTANT_REDIRECT = "https://my.home-assistant.io/redirect/oauth"
LISTEN_PORT = 8080


class RedirectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path != "/login":
            self.send_error(404, "Not Found")
            return

        query = parse_qs(parsed_path.query)
        query_flat = {k: v[0] for k, v in query.items()}
        query_str = urlencode(query_flat)

        redirect_url = f"{HOME_ASSISTANT_REDIRECT}?{query_str}"

        self.send_response(302)
        self.send_header("Location", redirect_url)
        self.end_headers()

        print(f"Redirected to: {redirect_url}")

    def log_message(self, format, *args):
        return  # Silence default logging


if __name__ == "__main__":
    server_address = ("127.0.0.1", LISTEN_PORT)
    httpd = HTTPServer(server_address, RedirectHandler)
    print(f"Relay server running on http://127.0.0.1:{LISTEN_PORT}/login")
    print("Press CTRL+C to quit the server when done")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nClosing relay server")
