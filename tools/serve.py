"""Local dev server for Polymarct.

Serves the site like http.server, and additionally accepts recordings:

    POST /_save/<filename>   ->  writes the body to tools/out/<filename>

That is what lets a film record itself in the page and land on disk as a real
file, instead of going through a browser download. Local only, no auth, not
something to run anywhere but this machine.

    python tools/serve.py [port]
"""
import os
import re
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tools", "out")
SAFE = re.compile(r"^[A-Za-z0-9._-]{1,120}$")


class Handler(SimpleHTTPRequestHandler):
    # keep-alive: a film render fires ~1800 POSTs back to back, and HTTP/1.0
    # closing every connection exhausts the socket table long before the end
    protocol_version = "HTTP/1.1"

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *args):
        if "_save" in (args[0] if args else ""):
            sys.stderr.write("[save] %s\n" % (args[0],))

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_POST(self):
        if not self.path.startswith("/_save/"):
            self.send_error(404)
            return
        name = os.path.basename(self.path[len("/_save/"):])
        if not SAFE.match(name):
            self.send_error(400, "bad filename")
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > 800 * 1024 * 1024:
            self.send_error(400, "bad length")
            return
        os.makedirs(OUT, exist_ok=True)
        path = os.path.join(OUT, name)
        remaining = length
        with open(path, "wb") as f:
            while remaining > 0:
                chunk = self.rfile.read(min(1 << 20, remaining))
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)
        size = os.path.getsize(path)
        sys.stderr.write("[save] %s  %.1f MB\n" % (name, size / 1e6))
        body = ('{"ok":true,"file":"%s","bytes":%d}' % (name, size)).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8099
    os.makedirs(OUT, exist_ok=True)
    print("polymarct dev server on http://localhost:%d  (recordings -> tools/out)" % port)
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    srv.request_queue_size = 128
    srv.daemon_threads = True
    srv.serve_forever()
