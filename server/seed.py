"""Seed the database from assets/js/data.js.

The browser simulation and the server must describe the same 50 markets, so the
questions, criteria, sources and deadlines are parsed out of the same file the
front end already ships rather than typed in twice.

    python server/seed.py            create missing markets
    python server/seed.py --reset    wipe the database first
"""
import os
import re
import sys
import json
import random

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)

import core
import markets as M
from amm import MICRO, YES, NO

DATA = os.path.join(ROOT, "assets", "js", "data.js")
HOUSE_EMAIL = "house@polymarct.local"
BOT_NAMES = ["kestrel", "lowdelta", "tapewatcher", "bidside", "quietbook",
             "vega_", "closeprint", "thinbook", "latefill", "oddsmith"]


def parse_markets():
    src = open(DATA, encoding="utf-8").read()
    body = src[src.index("const MARKETS"):src.index("/* Arc network telemetry")]
    out = []
    for m in re.finditer(r"\{\s*id:\"(.*?)\".*?\}(?=\s*,?\s*(?:\n\s*(?://[^\n]*\n\s*)*)?(?:\{|\]))", body, re.S):
        blob = m.group(0)

        def field(name, cast=str):
            mm = re.search(r'\b%s:\s*("(?:[^"\\]|\\.)*"|[-\d.]+)' % name, blob)
            if not mm:
                return None
            v = mm.group(1)
            if v.startswith('"'):
                v = json.loads(v)
            return cast(v)

        out.append({
            "id": field("id"), "cat": field("cat"), "q": field("q"),
            "yes": float(field("yes")), "ends": field("ends"),
            "src": field("src"), "crit": field("crit"),
        })
    return [m for m in out if m["id"] and m["q"] and m["crit"]]


def iso_to_epoch(s):
    import datetime
    return int(datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
               .replace(tzinfo=datetime.timezone.utc).timestamp())


def ensure_house():
    row = core.db().execute("SELECT id FROM users WHERE email=?", (HOUSE_EMAIL,)).fetchone()
    if row:
        return row["id"]
    pw = os.environ.get("POLYMARCT_HOUSE_PW") or core.secrets.token_urlsafe(24)
    uid = core.create_user("house", HOUSE_EMAIL, pw, is_admin=1)
    core.credit_user(uid, 5_000_000 * MICRO, "house_float")
    print("  house account created, password: %s" % pw)
    print("  (store it now, it is not shown again)")
    return uid


def main():
    if "--reset" in sys.argv and os.path.exists(core.DB_PATH):
        os.remove(core.DB_PATH)
        for suf in ("-wal", "-shm"):
            p = core.DB_PATH + suf
            if os.path.exists(p):
                os.remove(p)
        print("database wiped")

    core.init()
    house = ensure_house()
    rows = parse_markets()
    print("parsed %d markets from data.js" % len(rows))

    made = skipped = 0
    for r in rows:
        if core.db().execute("SELECT 1 FROM markets WHERE id=?", (r["id"],)).fetchone():
            skipped += 1
            continue
        closes = iso_to_epoch(r["ends"])
        if closes <= core.now() + 3600:
            closes = core.now() + 86400 * 30          # keep demo markets tradeable
        crit_no = ("NO if the condition above is not met before the resolution time, "
                   "including the case where the named source is discontinued and the "
                   "declared fallback shows no qualifying reading.")
        seed = 2_000 * MICRO
        price = min(0.95, max(0.05, r["yes"]))
        try:
            M.create_market(house, r["q"], r["cat"], r["crit"], crit_no,
                            r["src"], closes, seed, price, market_id=r["id"])
            made += 1
        except Exception as e:
            print("  skipped %s: %s" % (r["id"], e))
    print("created %d, already present %d" % (made, skipped))

    if "--traders" in sys.argv:
        seed_traders()

    bad = core.reconcile()
    print("ledger reconciles" if not bad else "LEDGER PROBLEM: %s" % bad)


def seed_traders():
    """A handful of accounts with real positions, so the board is not empty."""
    rng = random.Random(7)
    ids = [r["id"] for r in core.db().execute("SELECT id FROM markets WHERE status='open'")]
    for name in BOT_NAMES:
        row = core.db().execute("SELECT id FROM users WHERE handle=?", (name,)).fetchone()
        if row:
            uid = row["id"]
        else:
            uid = core.create_user(name, "%s@polymarct.local" % name, core.secrets.token_urlsafe(20))
            core.credit_user(uid, 20_000 * MICRO, "demo_float")
        for mid in rng.sample(ids, min(6, len(ids))):
            try:
                M.trade(uid, mid, rng.choice([YES, NO]), "buy",
                        amount=rng.randint(20, 400) * MICRO)
            except Exception:
                pass
    print("seeded %d demo traders" % len(BOT_NAMES))


if __name__ == "__main__":
    main()
