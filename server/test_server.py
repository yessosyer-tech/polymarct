"""Tests for the market engine.

Run against a throwaway database:

    python server/test_server.py

Money is checked two ways everywhere: the balance the user sees, and the ledger
that explains it. If those ever disagree the test fails, because a market whose
books do not add up is not a market.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ["POLYMARCT_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")

import amm
import core
import markets as M
from amm import YES, NO, MICRO

PASS = FAIL = 0


def check(cond, label):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print("  FAIL  %s" % label)


def approx(a, b, tol):
    return abs(a - b) <= tol


# ---------------------------------------------------------------- amm maths
def test_amm():
    print("amm")
    y, n = amm.seed(1000 * MICRO)
    check(approx(amm.price_yes(y, n), 0.5, 1e-9), "even seed prices at 0.5")

    # buying YES raises the YES price and never returns more than it should
    sh, fee, y2, n2 = amm.quote_buy(y, n, YES, 100 * MICRO, 0)
    p2 = amm.price_yes(y2, n2)
    check(p2 > 0.5, "buying YES moves the price up")
    check(sh > 100 * MICRO, "buying below a dollar returns more than one share per dollar")
    check(y2 * n2 >= y * n, "invariant does not shrink on a buy")

    # symmetry: the same spend on NO mirrors it
    sh_n, _, y3, n3 = amm.quote_buy(y, n, NO, 100 * MICRO, 0)
    check(approx(amm.price_yes(y3, n3), 1 - p2, 1e-6), "NO mirrors YES from an even book")
    check(sh_n == sh, "a mirrored trade returns the same share count")

    # a round trip costs money, it never prints it
    pay, fee2, y4, n4 = amm.quote_sell(y2, n2, YES, sh, 0)
    check(pay <= 100 * MICRO, "round trip cannot return more than it cost")
    check(approx(amm.price_yes(y4, n4), 0.5, 1e-4), "selling back returns the book to where it was")

    # fees land where they should
    sh_f, fee_f, _, _ = amm.quote_buy(y, n, YES, 100 * MICRO, 100)
    check(fee_f == 1 * MICRO, "1% fee on a 100 unit buy is 1 unit")
    check(sh_f < sh, "a fee means fewer shares for the same spend")

    # a big buy moves the price a lot but never off the rails
    big, _, y5, n5 = amm.quote_buy(y, n, YES, 100_000 * MICRO, 0)
    p5 = amm.price_yes(y5, n5)
    check(0 < p5 < 1, "price stays inside the unit interval after a huge buy")
    check(y5 > 0 and n5 > 0, "reserves stay positive")

    # opening away from even odds
    y6, n6, side, shares, spent = amm.open_at(1000 * MICRO, 0.67)
    check(approx(amm.price_yes(y6, n6), 0.67, 0.02), "open_at lands near the target price")
    check(side == YES and shares > 0, "the opener ends up holding the side they pushed")

    # bad input is refused, not absorbed
    for bad in (0, -5):
        try:
            amm.quote_buy(y, n, YES, bad, 0); check(False, "negative buy refused")
        except amm.AmmError:
            check(True, "negative buy refused")
    # an oversized sell is not an error, it is a terrible price. What must hold
    # is that the pool can always cover what it promised to pay.
    huge = 1000 * MICRO * 1000
    try:
        pay_h, _, y_h, n_h = amm.quote_sell(y, n, YES, huge, 0)
        check(pay_h < min(y, n), "a huge sell cannot drain more than the pool holds")
        check(pay_h < huge, "a huge sell pays far less than face value")
        check(y_h > 0 and n_h > 0, "the pool survives a huge sell")
    except amm.AmmError:
        check(True, "a huge sell is refused outright")


# ---------------------------------------------------------------- accounts
def test_accounts():
    print("accounts")
    core.init()
    uid = core.create_user("alice", "alice@example.com", "correct horse battery")
    check(uid > 0, "signup works")
    for bad in [("al", "a@b.co", "correct horse battery"),
                ("bob", "nope", "correct horse battery"),
                ("bob", "b@b.co", "short")]:
        try:
            core.create_user(*bad); check(False, "rejected %s" % (bad,))
        except ValueError:
            check(True, "rejected %s" % (bad,))
    try:
        core.create_user("alice", "other@example.com", "correct horse battery")
        check(False, "duplicate handle refused")
    except ValueError:
        check(True, "duplicate handle refused")

    check(core.login("alice@example.com", "correct horse battery") == uid, "login works")
    check(core.login("alice@example.com", "wrong") is None, "wrong password refused")
    check(core.login("ALICE@example.com", "correct horse battery") == uid, "email is case insensitive")

    tok = core.new_session(uid)
    check(core.user_for_token(tok)["id"] == uid, "session resolves")
    core.drop_session(tok)
    check(core.user_for_token(tok) is None, "logout kills the session")

    core.faucet(uid)
    bal = core.db().execute("SELECT balance FROM users WHERE id=?", (uid,)).fetchone()["balance"]
    check(bal == core.FAUCET, "faucet credits once")
    try:
        core.faucet(uid); check(False, "faucet cooldown holds")
    except ValueError:
        check(True, "faucet cooldown holds")
    check(not core.reconcile(), "ledger reconciles after account setup")
    return uid


# ---------------------------------------------------------------- markets
def test_market_flow(uid):
    print("market flow")
    core.credit_user(uid, 50_000 * MICRO, "test_topup")

    bad = M.validate_spec("Will BTC pump soon", "yes if", "no if", "twitter",
                          core.now() + 100, 10 * MICRO)
    check(len(bad) >= 4, "a vague question fails several checks")
    good = M.validate_spec(
        "Will BTC reach $125,000 before October 31?",
        "YES if the hourly close on Coinbase BTC-USD prints at or above $125,000.00 before the deadline.",
        "NO if no such close occurs before the deadline, including if the feed is discontinued.",
        "Coinbase BTC-USD spot, hourly close", core.now() + 86400, 1000 * MICRO)
    check(good == [], "a well formed question passes")

    mid = M.create_market(
        uid, "Will BTC reach $125,000 before October 31?", "CRYPTO",
        "YES if the hourly close on Coinbase BTC-USD prints at or above $125,000.00 before the deadline.",
        "NO if no such close occurs before the deadline, including if the feed is discontinued.",
        "Coinbase BTC-USD spot, hourly close", core.now() + 86400, 1000 * MICRO, 0.67)
    row = M.market_row(mid)
    check(row["status"] == "open", "market opens")
    check(approx(amm.price_yes(row["y_reserve"], row["n_reserve"]), 0.67, 0.02), "opens near 67 cents")
    check(len(row["spec_hash"]) == 64, "the spec is hashed at creation")
    check(not core.reconcile(), "ledger reconciles after creation")

    bob = core.create_user("bob", "bob@example.com", "correct horse battery")
    core.credit_user(bob, 10_000 * MICRO, "test_topup")

    before = core.db().execute("SELECT balance FROM users WHERE id=?", (bob,)).fetchone()["balance"]
    t = M.trade(bob, mid, YES, "buy", amount=500 * MICRO)
    after = core.db().execute("SELECT balance FROM users WHERE id=?", (bob,)).fetchone()["balance"]
    check(before - after == 500 * MICRO, "a buy debits exactly what was spent")
    check(t["shares"] > 0, "a buy returns shares")
    pos = core.db().execute("SELECT * FROM positions WHERE user_id=? AND market_id=?", (bob, mid)).fetchone()
    check(pos["yes_shares"] == t["shares"], "the position records the shares")

    try:
        M.trade(bob, mid, YES, "sell", shares=pos["yes_shares"] * 2)
        check(False, "cannot sell shares you do not hold")
    except M.MarketError:
        check(True, "cannot sell shares you do not hold")

    half = pos["yes_shares"] // 2
    s = M.trade(bob, mid, YES, "sell", shares=half)
    check(s["collateral"] > 0, "a sell pays out")
    pos2 = core.db().execute("SELECT * FROM positions WHERE user_id=? AND market_id=?", (bob, mid)).fetchone()
    check(pos2["yes_shares"] == pos["yes_shares"] - half, "the position shrinks by what was sold")
    check(not core.reconcile(), "ledger reconciles after trading")

    poor = core.create_user("poor", "poor@example.com", "correct horse battery")
    try:
        M.trade(poor, mid, YES, "buy", amount=100 * MICRO)
        check(False, "cannot trade without balance")
    except ValueError:
        check(True, "cannot trade without balance")

    return mid, bob


def test_settlement(mid, bob):
    print("resolution and settlement")
    admin = core.create_user("oracle", "oracle@example.com", "correct horse battery", is_admin=1)

    try:
        M.settle(mid); check(False, "cannot settle before resolving")
    except M.MarketError:
        check(True, "cannot settle before resolving")

    try:
        M.resolve(mid, YES, "", admin); check(False, "a verdict needs evidence")
    except M.MarketError:
        check(True, "a verdict needs evidence")

    M.resolve(mid, YES, "Coinbase BTC-USD hourly close printed $125,412.00", admin)
    row = M.market_row(mid)
    check(row["status"] == "resolved" and row["outcome"] == YES, "resolution records the outcome")

    try:
        M.settle(mid); check(False, "dispute window holds settlement")
    except M.MarketError:
        check(True, "dispute window holds settlement")

    d = M.open_dispute(bob, mid, "The fallback source was never read before resolving.")
    check(d["dispute_id"] > 0, "a position holder can dispute")
    core.db().execute("UPDATE markets SET settles_at=? WHERE id=?", (core.now() - 1, mid))
    try:
        M.settle(mid); check(False, "an open dispute blocks settlement")
    except M.MarketError:
        check(True, "an open dispute blocks settlement")
    M.decide_dispute(d["dispute_id"], upheld=False)
    check(not core.reconcile(), "ledger reconciles after a dispute")

    held = core.db().execute("SELECT yes_shares FROM positions WHERE user_id=? AND market_id=?",
                             (bob, mid)).fetchone()["yes_shares"]
    before = core.db().execute("SELECT balance FROM users WHERE id=?", (bob,)).fetchone()["balance"]
    out = M.settle(mid)
    after = core.db().execute("SELECT balance FROM users WHERE id=?", (bob,)).fetchone()["balance"]
    check(after - before == held, "a winning share pays exactly one unit")
    check(M.market_row(mid)["status"] == "settled", "the market ends settled")
    check(M.settle(mid).get("already"), "settlement is idempotent")
    check(not core.reconcile(), "ledger reconciles after settlement")

    p = M.portfolio(bob)
    check(p["balance"] == after, "portfolio reports the real balance")
    check(any(x["market"] == mid for x in p["positions"]), "the settled position is visible")


def test_closed_market(uid):
    print("deadlines")
    mid = M.create_market(
        uid, "Will this test market close before the deadline passes?", "CRYPTO",
        "YES if the deadline passes while this test is running, which it will.",
        "NO if the deadline somehow does not pass, which cannot happen here.",
        "The system clock on the test runner", core.now() + 7200, 600 * MICRO, 0.5)
    core.db().execute("UPDATE markets SET closes_at=? WHERE id=?", (core.now() - 1, mid))
    M.close_due()
    check(M.market_row(mid)["status"] == "closed", "a market past its deadline closes")
    try:
        M.trade(uid, mid, YES, "buy", amount=10 * MICRO)
        check(False, "a closed market refuses trades")
    except M.MarketError:
        check(True, "a closed market refuses trades")


def main():
    test_amm()
    uid = test_accounts()
    mid, bob = test_market_flow(uid)
    test_settlement(mid, bob)
    test_closed_market(uid)
    print("\n%d passed, %d failed" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
