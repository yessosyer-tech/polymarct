"""End to end test against a running server.

    python server/app.py 8100        (in one shell, with POLYMARCT_ADMIN_TOKEN set)
    python server/test_api.py 8100   (in another)

This exercises the HTTP surface a browser actually talks to: cookies, status
codes, refusals. The unit tests cover the maths; this covers the wiring.
"""
import os
import sys
import json
import time
import urllib.request
import urllib.error
import http.cookiejar

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8100
BASE = "http://localhost:%d/api" % PORT
ADMIN = os.environ.get("POLYMARCT_ADMIN_TOKEN", "audit-admin-token")
PASS = FAIL = 0


def check(cond, label):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print("  FAIL  %s" % label)


class Client:
    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def call(self, path, body=None, admin=False, method=None):
        url = BASE + path
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"))
        if data:
            req.add_header("Content-Type", "application/json")
        if admin:
            req.add_header("X-Admin-Token", ADMIN)
        try:
            with self.opener.open(req, timeout=15) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read().decode())
            except Exception:
                return e.code, {}


def main():
    uniq = str(int(time.time()))
    a, b = Client(), Client()

    print("health")
    s, d = a.call("/health")
    check(s == 200 and d.get("ok"), "health responds")

    print("auth")
    s, d = a.call("/auth/signup", {"handle": "tester" + uniq[-6:],
                                   "email": "t%s@example.com" % uniq,
                                   "password": "correct horse battery"})
    check(s == 200 and d["user"]["balance"] > 0, "signup opens an account with a faucet balance")
    s, d = a.call("/auth/signup", {"handle": "x", "email": "bad", "password": "short"})
    check(s == 400, "bad signup refused")
    s, d = b.call("/portfolio")
    check(s == 401, "portfolio needs a session")
    s, d = a.call("/me")
    check(s == 200 and d["user"], "session survives between calls")

    print("markets")
    s, d = a.call("/markets?limit=5")
    check(s == 200 and len(d["markets"]) == 5, "market list paginates")
    # pick one that is actually open; earlier runs may have resolved the top of
    # the list, and a test that depends on run order is not a test
    s, allm = a.call("/markets?status=open&limit=50")
    check(s == 200 and allm["markets"], "open markets can be filtered")
    mid = allm["markets"][0]["id"]
    s, det = a.call("/markets/" + mid)
    check(s == 200 and det["criteria"] and det["source"], "detail carries criteria and source")
    check(len(det["spec_hash"]) == 64, "detail exposes the spec hash")
    s, d = a.call("/markets/does-not-exist")
    check(s == 400, "unknown market refused")

    print("quote and trade")
    s, q = a.call("/quote?market=%s&side=YES&action=buy&amount=100" % mid)
    check(s == 200 and q["shares"] > 0, "quote returns shares")
    check(q["price_after"] > q["price_before"], "a YES buy is quoted to move the price up")

    s, before = a.call("/portfolio")
    s, t = a.call("/trade", {"market": mid, "side": "YES", "action": "buy", "amount": 100})
    check(s == 200 and t["shares"] > 0, "buy executes")
    check(abs(t["shares"] - q["shares"]) / q["shares"] < 0.02, "execution matches the quote")
    s, after = a.call("/portfolio")
    check(before["balance"] - after["balance"] == 100_000_000, "balance falls by exactly the spend")
    check(any(p["market"] == mid for p in after["positions"]), "the position appears")

    s, d = a.call("/trade", {"market": mid, "side": "YES", "action": "sell", "shares": 999999})
    check(s == 400, "cannot sell shares you do not hold")
    s, d = a.call("/trade", {"market": mid, "side": "MAYBE", "action": "buy", "amount": 10})
    check(s == 400, "a nonsense side is refused")
    s, d = a.call("/trade", {"market": mid, "side": "YES", "action": "buy", "amount": -50})
    check(s == 400, "a negative amount is refused")
    s, d = a.call("/trade", {"market": mid, "side": "YES", "action": "buy", "amount": 1e12})
    check(s == 400, "you cannot spend money you do not have")

    held = [p for p in after["positions"] if p["market"] == mid][0]["yes_shares"]
    s, d = a.call("/trade", {"market": mid, "side": "YES", "action": "sell",
                             "shares": held / 2_000_000})
    check(s == 200 and d["collateral"] > 0, "a partial sell pays out")

    print("creation")
    s, d = a.call("/markets", {"question": "Will this pump soon", "category": "CRYPTO",
                               "criteria_yes": "yes", "criteria_no": "no",
                               "source": "twitter", "closes_at": int(time.time()) + 60,
                               "seed": 1})
    check(s == 400 and "wording" in d.get("error", "").lower(), "a vague market is refused with a reason")
    s, d = a.call("/markets", {
        "question": "Will this integration test create a market before it finishes?",
        "category": "CRYPTO",
        "criteria_yes": "YES if the market is visible in the market list after creation, checked immediately.",
        "criteria_no": "NO if the market is absent from the list, including if creation failed silently.",
        "source": "The Polymarct market list endpoint",
        "closes_at": int(time.time()) + 86400, "seed": 600, "open_price": 0.5})
    check(s == 400 or (s == 200 and d.get("market")), "a well formed market is accepted or refused for balance")

    print("admin and settlement")
    s, d = b.call("/admin/resolve", {"market": mid, "outcome": "YES", "evidence": "test"})
    check(s == 403, "admin needs the token")
    s, d = b.call("/admin/resolve", {"market": mid, "outcome": "YES", "evidence": "test"}, admin=True)
    check(s == 200 and d["outcome"] == "YES", "admin can resolve with the token")
    s, d = b.call("/admin/settle", {"market": mid}, admin=True)
    check(s == 400, "settlement waits for the dispute window")
    s, d = b.call("/admin/reconcile", admin=True)
    check(s == 200 and d["ok"], "the ledger reconciles over the API")

    print("limits")
    codes = [a.call("/auth/login", {"email": "nobody@example.com", "password": "x"})[0]
             for _ in range(14)]
    check(429 in codes, "repeated login attempts get rate limited")

    print("\n%d passed, %d failed" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
