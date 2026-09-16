"""Photograph the real site, headless, straight to PNG.

    python tools/shots.py

Serves the project on a local port, drives Chrome with no window, and writes
one tall capture per page into tools/_shots/. Tall on purpose: a 1920x2600
capture holds the whole page, so panning a 1080-high window down it gives a
real scroll through real pixels, with no second capture pass.

These are the backplates for the site tour film and for the content cards.
Nothing here is a mock up. It is the site.
"""
import os
import sys
import time
import shutil
import subprocess
import threading
import http.server
import socketserver

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "_shots")
PORT = 8123
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# page, capture height, what it is for
PAGES = [
    ("index",       2600, "the hero and the live field"),
    ("markets",     2800, "the board, every open market"),
    ("market",      2800, "one market: chart, book, trade panel"),
    ("discover",    2600, "what moved, and why"),
    ("signals",     2400, "momentum, early, contrarian"),
    ("map",         2200, "the market map"),
    ("arc",         2400, "why Arc, and USDC only"),
    ("leaderboard", 2400, "who is actually right"),
    ("verdict",     2600, "the resolution engine"),
    ("create",      2600, "publish your own question"),
    ("token",       2600, "$PMARC"),
    ("portfolio",   2200, "your positions"),
]


class Quiet(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def translate_path(self, path):
        rel = path.split("?", 1)[0].split("#", 1)[0].lstrip("/")
        return os.path.join(ROOT, rel.replace("/", os.sep))


def serve():
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", PORT), Quiet)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def shoot(page, height):
    dst = os.path.join(OUT, page + ".png")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", "--virtual-time-budget=7000",
                    "--window-size=1920,%d" % height,
                    "--screenshot=" + dst,
                    "http://127.0.0.1:%d/%s.html" % (PORT, page)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return dst


def main():
    if not os.path.exists(CHROME):
        print("Chrome not found at %s" % CHROME)
        return 1
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    srv = serve()
    time.sleep(0.6)
    try:
        for page, h, note in PAGES:
            if not os.path.exists(os.path.join(ROOT, page + ".html")):
                print("  skip %-12s (no page)" % page)
                continue
            p = shoot(page, h)
            kb = os.path.getsize(p) / 1024 if os.path.exists(p) else 0
            print("  %-12s %5d px  %6.0f KB   %s" % (page, h, kb, note))
    finally:
        srv.shutdown()
    print("shots in %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
