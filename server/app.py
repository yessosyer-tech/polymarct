"""Polymarct application server.

Serves the site and a JSON API from one process, stdlib only.

    python server/app.py [port]

Environment:
    POLYMARCT_DB          sqlite path (default server/polymarct.db)
    POLYMARCT_FEE_BPS     protocol fee on the collateral leg, default 100 = 1%
    POLYMARCT_ADMIN_TOKEN required for /api/admin/*; without it admin is closed

Demo money. Balances are issued by a faucet and settle inside this database.
Nothing here touches a chain, custody or real funds.
"""
import os
import re
import sys
import json
import time
import http.cookies
import threading
import traceback
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import core
import markets as M
from amm import MICRO, YES, NO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADMIN_TOKEN = os.environ.get("POLYMARCT_ADMIN_TOKEN", "")
MAX_BODY = 256 * 1024

# --------------------------------------------------------------- rate limit
_buckets = {}
_bucket_lock = threading.Lock()
LIMITS = {"default": (120, 60), "write": (30, 60), "auth": (10, 300)}


def allow(ip, kind):
    cap, per = LIMITS[kind]
    key = (ip, kind)
    t = time.time()
    with _bucket_lock:
        tokens, last = _buckets.get(key, (cap, t))
        tokens = min(cap, tokens + (t - last) * cap / per)
        if tokens < 1:
            _buckets[key] = (tokens, t)
            return False
        _buckets[key] = (tokens - 1, t)
        return True


class ApiError(Exception):
    def __init__(self, msg, status=400):
        super().__init__(msg)
        self.status = status


def money(v):
    """Accept a decimal string or number of USDC, return micro units."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        raise ApiError("not a number")
    if f != f or f in (float("inf"), float("-inf")):
        raise ApiError("not a number")
    return int(round(f * MICRO))


class Handler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "polymarct"

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *args):
        if os.environ.get("POLYMARCT_VERBOSE"):
            sys.stderr.write("%s\n" % (fmt % args))

    # ------------------------------------------------------------ helpers
    @property
    def ip(self):
        return self.client_address[0]

    def cookies(self):
        c = http.cookies.SimpleCookie()
        c.load(self.headers.get("Cookie", ""))
        return {k: v.value for k, v in c.items()}

    def current_user(self):
        return core.user_for_token(self.cookies().get("pm_session"))

    def require_user(self):
        u = self.current_user()
        if not u:
            raise ApiError("sign in first", 401)
        return u

    def require_admin(self):
        if not ADMIN_TOKEN:
            raise ApiError("admin is closed on this instance", 403)
        if self.headers.get("X-Admin-Token", "") != ADMIN_TOKEN:
            raise ApiError("bad admin token", 403)
        u = self.current_user()
        return u["id"] if u else None

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        if n > MAX_BODY:
            raise ApiError("body too large", 413)
        raw = self.rfile.read(n)
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            raise ApiError("body must be JSON")
        if not isinstance(data, dict):
            raise ApiError("body must be a JSON object")
        return data

    def send_json(self, obj, status=200, cookie=None):
        payload = json.dumps(obj, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(payload)

    def end_headers(self):
        if not self.path.startswith("/api/"):
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "same-origin")
        super().end_headers()

    # ------------------------------------------------------------ routing
    def do_GET(self):
        if self.path.startswith("/api/"):
            return self.api("GET")
        return super().do_GET()

    def do_HEAD(self):
        if self.path.startswith("/api/"):
            return self.api("GET")
        return super().do_HEAD()

    def do_POST(self):
        if self.path.startswith("/api/"):
            return self.api("POST")
        self.send_error(404)

    def api(self, method):
        u = urlparse(self.path)
        path = u.path[len("/api"):].rstrip("/") or "/"
        query = parse_qs(u.query)
        kind = "auth" if path.startswith("/auth") else ("write" if method == "POST" else "default")
        if not allow(self.ip, kind):
            return self.send_json({"error": "slow down"}, 429)
        # a JSON body plus SameSite cookies is enough to stop a form post from
        # another origin; anything cross origin cannot read the reply either
        if method == "POST":
            ct = (self.headers.get("Content-Type") or "").split(";")[0].strip()
            if ct and ct != "application/json":
                return self.send_json({"error": "content type must be application/json"}, 415)
        try:
            out = self.route(method, path, query)
            if isinstance(out, tuple):
                body, cookie = out
                return self.send_json(body, 200, cookie)
            return self.send_json(out)
        except ApiError as e:
            return self.send_json({"error": str(e)}, e.status)
        except (M.MarketError, ValueError) as e:
            return self.send_json({"error": str(e)}, 400)
        except Exception:
            traceback.print_exc()
            return self.send_json({"error": "server error"}, 500)

    # ------------------------------------------------------------ endpoints
    def route(self, method, path, q):
        b = self.body() if method == "POST" else {}

        if path == "/health":
            return {"ok": True, "markets": core.db().execute(
                "SELECT COUNT(*) c FROM markets").fetchone()["c"], "fee_bps": core.FEE_BPS}

        # ---- auth
        if path == "/auth/signup" and method == "POST":
            uid = core.create_user(b.get("handle"), b.get("email"), b.get("password"))
            core.faucet(uid)
            return self.session_reply(uid)
        if path == "/auth/login" and method == "POST":
            uid = core.login(b.get("email"), b.get("password"))
            if not uid:
                raise ApiError("wrong email or password", 401)
            return self.session_reply(uid)
        if path == "/auth/logout" and method == "POST":
            core.drop_session(self.cookies().get("pm_session"))
            return ({"ok": True}, "pm_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict")
        if path == "/me":
            u = self.current_user()
            if not u:
                return {"user": None}
            return {"user": {"handle": u["handle"], "balance": u["balance"],
                             "is_admin": bool(u["is_admin"])}}
        if path == "/faucet" and method == "POST":
            u = self.require_user()
            amt = core.faucet(u["id"])
            return {"credited": amt, "balance": core.db().execute(
                "SELECT balance FROM users WHERE id=?", (u["id"],)).fetchone()["balance"]}

        # ---- markets
        if path == "/markets" and method == "GET":
            M.close_due()
            return {"markets": M.list_markets(
                status=(q.get("status") or [None])[0],
                category=(q.get("category") or [None])[0],
                limit=int((q.get("limit") or [100])[0]),
                offset=int((q.get("offset") or [0])[0]))}
        if path == "/markets" and method == "POST":
            u = self.require_user()
            mid = M.create_market(
                u["id"], b.get("question", ""), b.get("category", "CRYPTO"),
                b.get("criteria_yes", ""), b.get("criteria_no", ""), b.get("source", ""),
                int(b.get("closes_at") or 0), money(b.get("seed", 0)),
                float(b.get("open_price") or 0.5))
            return {"market": mid}

        m = re.match(r"^/markets/([a-z0-9-]{1,64})$", path)
        if m and method == "GET":
            row = M.market_row(m.group(1))
            d = M.public(row, deep=True)
            d["trades"] = [dict(t) for t in core.db().execute(
                """SELECT t.side,t.action,t.shares,t.collateral,t.price_after,t.created_at,u.handle
                   FROM trades t JOIN users u ON u.id=t.user_id
                   WHERE t.market_id=? ORDER BY t.id DESC LIMIT 25""", (m.group(1),))]
            return d

        if path == "/quote":
            mid = (q.get("market") or [""])[0]
            side = (q.get("side") or ["YES"])[0].upper()
            action = (q.get("action") or ["buy"])[0]
            if action == "buy":
                return M.quote(mid, side, "buy", amount=money((q.get("amount") or ["0"])[0]))
            return M.quote(mid, side, "sell", shares=int(float((q.get("shares") or ["0"])[0]) * MICRO))

        if path == "/trade" and method == "POST":
            u = self.require_user()
            side = str(b.get("side", "")).upper()
            action = str(b.get("action", "buy"))
            if action == "buy":
                return M.trade(u["id"], b.get("market"), side, "buy", amount=money(b.get("amount", 0)))
            return M.trade(u["id"], b.get("market"), side, "sell",
                           shares=int(round(float(b.get("shares", 0)) * MICRO)))

        # ---- account
        if path == "/portfolio":
            u = self.require_user()
            return M.portfolio(u["id"])
        if path == "/leaderboard":
            return {"traders": M.leaderboard(int((q.get("limit") or [20])[0]))}
        if path == "/ledger":
            u = self.require_user()
            return {"entries": [dict(r) for r in core.db().execute(
                "SELECT delta,reason,ref,created_at FROM ledger WHERE user_id=? ORDER BY id DESC LIMIT 100",
                (u["id"],))]}

        # ---- disputes
        if path == "/dispute" and method == "POST":
            u = self.require_user()
            return M.open_dispute(u["id"], b.get("market"), b.get("reason", ""))

        # ---- admin, the oracle side of the house
        if path == "/admin/resolve" and method == "POST":
            uid = self.require_admin()
            return M.resolve(b.get("market"), str(b.get("outcome", "")).upper(),
                             b.get("evidence", ""), uid)
        if path == "/admin/settle" and method == "POST":
            self.require_admin()
            return M.settle(b.get("market"))
        if path == "/admin/dispute" and method == "POST":
            self.require_admin()
            return M.decide_dispute(int(b.get("id")), bool(b.get("upheld")),
                                    b.get("outcome"), b.get("evidence"))
        if path == "/admin/reconcile":
            self.require_admin()
            bad = core.reconcile()
            return {"ok": not bad, "problems": bad}

        raise ApiError("no such endpoint", 404)

    def session_reply(self, uid):
        token = core.new_session(uid)
        u = core.db().execute("SELECT handle,balance,is_admin FROM users WHERE id=?", (uid,)).fetchone()
        cookie = ("pm_session=%s; Path=/; Max-Age=%d; HttpOnly; SameSite=Strict"
                  % (token, core.SESSION_TTL))
        return ({"user": {"handle": u["handle"], "balance": u["balance"],
                          "is_admin": bool(u["is_admin"])}}, cookie)


def sweeper():
    """Close markets that are past their deadline, settle what is due."""
    while True:
        try:
            core.init()
            M.close_due()
            for r in core.db().execute(
                    "SELECT id FROM markets WHERE status='resolved' AND settles_at<=?", (core.now(),)):
                try:
                    M.settle(r["id"])
                except M.MarketError:
                    pass
        except Exception:
            traceback.print_exc()
        time.sleep(30)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8099
    core.init()
    t = threading.Thread(target=sweeper, daemon=True)
    t.start()
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    srv.daemon_threads = True
    srv.request_queue_size = 128
    print("polymarct on http://localhost:%d" % port)
    print("  api    http://localhost:%d/api/health" % port)
    print("  admin  %s" % ("enabled" if ADMIN_TOKEN else "closed, set POLYMARCT_ADMIN_TOKEN"))
    srv.serve_forever()


if __name__ == "__main__":
    main()
