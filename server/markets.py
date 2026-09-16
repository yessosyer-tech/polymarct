"""Market lifecycle: create, trade, close, resolve, settle, dispute.

Money only moves through core.credit_user / debit_user / account_move, so the
ledger is complete by construction. Trading and settlement each run inside one
SQLite transaction; a failure part way through leaves no half applied trade.
"""
import re
import json

import amm
import core
from amm import YES, NO, MICRO
from core import db, now, ledger, credit_user, debit_user, account_move, HOUSE

VAGUE = ["soon", "a lot", "significant", "major", "many", "big", "moon", "pump",
         "probably", "might", "could", "fair", "good", "bad", "best", "better",
         "successful", "popular", "important", "huge", "massive"]
BAD_SOURCE = re.compile(r"twitter|x\.com|telegram|vibes|community|discord", re.I)
ID_RE = re.compile(r"^[a-z0-9-]{3,48}$")


class MarketError(Exception):
    pass


# ---------------------------------------------------------------- reads

def market_row(mid):
    r = db().execute("SELECT * FROM markets WHERE id=?", (mid,)).fetchone()
    if not r:
        raise MarketError("no such market")
    return r


def public(row, deep=False):
    y, n = row["y_reserve"], row["n_reserve"]
    p = amm.price_yes(y, n)
    out = {
        "id": row["id"], "question": row["question"], "category": row["category"],
        "price": round(p, 4), "yes_cents": round(p * 100, 1), "no_cents": round((1 - p) * 100, 1),
        "status": row["status"], "closes_at": row["closes_at"],
        "volume": row["volume"], "liquidity": min(y, n),
        "outcome": row["outcome"],
    }
    if deep:
        out.update({
            "criteria": row["criteria"], "source": row["source"],
            "spec_hash": row["spec_hash"], "evidence": row["evidence"],
            "resolved_at": row["resolved_at"], "settles_at": row["settles_at"],
            "reserves": {"yes": y, "no": n},
            "traders": db().execute(
                "SELECT COUNT(DISTINCT user_id) c FROM trades WHERE market_id=?", (row["id"],)).fetchone()["c"],
        })
    return out


def list_markets(status=None, category=None, limit=100, offset=0):
    q = "SELECT * FROM markets WHERE 1=1"
    args = []
    if status:
        q += " AND status=?"; args.append(status)
    if category:
        q += " AND category=?"; args.append(category)
    q += " ORDER BY volume DESC, closes_at ASC LIMIT ? OFFSET ?"
    args += [min(int(limit), 200), int(offset)]
    return [public(r) for r in db().execute(q, args)]


# ---------------------------------------------------------------- create

def validate_spec(question, criteria_yes, criteria_no, source, closes_at, seed):
    errs = []
    q = (question or "").strip()
    if len(q) < 15 or not q.endswith("?"):
        errs.append("The question must be a single closed question ending in a question mark.")
    low = q.lower()
    hit = [v for v in VAGUE if v in low]
    if hit:
        errs.append("Remove subjective wording: " + ", ".join(sorted(set(hit))) + ".")
    if not re.search(r"\b(before|by|during|on or before|this|next)\b", q, re.I):
        errs.append("The question itself must state the window, not only the date field.")
    if not closes_at or closes_at < now() + 3600:
        errs.append("Resolution time must be at least an hour from now.")
    if len((source or "").strip()) < 10 or BAD_SOURCE.search(source or ""):
        errs.append("Name a specific feed, filing or publication. Social platforms are not a source.")
    if len((criteria_yes or "").strip()) < 40 or "yes" not in (criteria_yes or "").lower():
        errs.append("State exactly what makes it YES, including the threshold.")
    if len((criteria_no or "").strip()) < 40 or "no" not in (criteria_no or "").lower():
        errs.append("State exactly what makes it NO, including the missing data case.")
    if seed < core.MIN_SEED:
        errs.append("Seed at least %d USDC so the opening book is tradeable." % (core.MIN_SEED // MICRO))
    return errs


def slugify(question):
    s = re.sub(r"[^a-z0-9]+", "-", question.lower()).strip("-")[:40]
    return s or "market"


def create_market(uid, question, category, criteria_yes, criteria_no, source,
                  closes_at, seed, open_price=0.5, market_id=None):
    errs = validate_spec(question, criteria_yes, criteria_no, source, closes_at, seed)
    if errs:
        raise MarketError(" ".join(errs))

    total = seed + core.CREATOR_BOND
    row = db().execute("SELECT balance FROM users WHERE id=?", (uid,)).fetchone()
    if not row or row["balance"] < total:
        raise MarketError("you need %d USDC: %d seed plus a %d bond"
                          % (total // MICRO, seed // MICRO, core.CREATOR_BOND // MICRO))

    # a caller may pin the id so links stay stable with the front end; renaming
    # afterwards would break the foreign keys that point at it
    mid = market_id or slugify(question)
    if not ID_RE.match(mid):
        raise MarketError("bad market id")
    n = 1
    base = mid
    while db().execute("SELECT 1 FROM markets WHERE id=?", (mid,)).fetchone():
        if market_id:
            raise MarketError("a market with that id already exists")
        n += 1
        mid = "%s-%d" % (base, n)

    criteria = json.dumps({"yes": criteria_yes.strip(), "no": criteria_no.strip()})
    sh = core.spec_hash(question, criteria, source, closes_at)

    y, nn, side, shares, spent = amm.open_at(seed, open_price, 0)

    with core._write_lock:
        db().execute("BEGIN IMMEDIATE")
        try:
            debit_user(uid, total, "market_create", mid)
            account_move("escrow", seed, "market_seed", mid)
            account_move("escrow", core.CREATOR_BOND, "creator_bond", mid)
            db().execute(
                """INSERT INTO markets(id,question,category,criteria,source,closes_at,created_by,
                   created_at,y_reserve,n_reserve,seed,status,spec_hash,volume)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,'open',?,0)""",
                (mid, question.strip(), category, criteria, source.strip(), closes_at, uid,
                 now(), y, nn, seed, sh))
            if shares > 0:
                db().execute(
                    """INSERT INTO positions(user_id,market_id,yes_shares,no_shares,cost)
                       VALUES(?,?,?,?,?)""",
                    (uid, mid, shares if side == YES else 0, shares if side == NO else 0, 0))
            db().execute("COMMIT")
        except Exception:
            db().execute("ROLLBACK")
            raise
    return mid


# ---------------------------------------------------------------- trade

def quote(mid, side, action, amount=None, shares=None):
    r = market_row(mid)
    y, n = r["y_reserve"], r["n_reserve"]
    if action == "buy":
        sh, fee, y2, n2 = amm.quote_buy(y, n, side, amount, core.FEE_BPS)
        return {"shares": sh, "collateral": amount, "fee": fee,
                "avg_price": round(amount / sh, 6) if sh else 0,
                "price_before": round(amm.price_yes(y, n), 4),
                "price_after": round(amm.price_yes(y2, n2), 4)}
    pay, fee, y2, n2 = amm.quote_sell(y, n, side, shares, core.FEE_BPS)
    return {"shares": shares, "collateral": pay, "fee": fee,
            "avg_price": round(pay / shares, 6) if shares else 0,
            "price_before": round(amm.price_yes(y, n), 4),
            "price_after": round(amm.price_yes(y2, n2), 4)}


def trade(uid, mid, side, action, amount=None, shares=None):
    if side not in (YES, NO):
        raise MarketError("side must be YES or NO")
    if action not in ("buy", "sell"):
        raise MarketError("action must be buy or sell")

    with core._write_lock:
        db().execute("BEGIN IMMEDIATE")
        try:
            r = market_row(mid)
            if r["status"] != "open":
                raise MarketError("this market is %s" % r["status"])
            if r["closes_at"] <= now():
                db().execute("UPDATE markets SET status='closed' WHERE id=?", (mid,))
                raise MarketError("this market has closed")

            y, n = r["y_reserve"], r["n_reserve"]
            pos = db().execute("SELECT * FROM positions WHERE user_id=? AND market_id=?",
                               (uid, mid)).fetchone()

            if action == "buy":
                amount = int(amount or 0)
                if amount < MICRO // 100:
                    raise MarketError("minimum trade is 0.01 USDC")
                sh, fee, y2, n2 = amm.quote_buy(y, n, side, amount, core.FEE_BPS)
                debit_user(uid, amount, "trade_buy", mid)
                account_move("escrow", amount - fee, "trade_collateral", mid)
                account_move("fees", fee, "trade_fee", mid)
                dy = sh if side == YES else 0
                dn = sh if side == NO else 0
                cost = amount
                traded = amount
            else:
                shares = int(shares or 0)
                held = (pos["yes_shares"] if side == YES else pos["no_shares"]) if pos else 0
                if shares <= 0 or shares > held:
                    raise MarketError("you do not hold that many shares")
                pay, fee, y2, n2 = amm.quote_sell(y, n, side, shares, core.FEE_BPS)
                credit_user(uid, pay, "trade_sell", mid)
                account_move("escrow", -(pay + fee), "trade_collateral", mid)
                account_move("fees", fee, "trade_fee", mid)
                dy = -shares if side == YES else 0
                dn = -shares if side == NO else 0
                cost = -pay
                sh = shares
                traded = pay

            if pos:
                db().execute(
                    """UPDATE positions SET yes_shares=yes_shares+?, no_shares=no_shares+?,
                       cost=cost+? WHERE user_id=? AND market_id=?""",
                    (dy, dn, cost, uid, mid))
            else:
                db().execute(
                    "INSERT INTO positions(user_id,market_id,yes_shares,no_shares,cost) VALUES(?,?,?,?,?)",
                    (uid, mid, max(dy, 0), max(dn, 0), cost))

            price_after = amm.price_yes(y2, n2)
            db().execute("UPDATE markets SET y_reserve=?, n_reserve=?, volume=volume+? WHERE id=?",
                         (y2, n2, traded, mid))
            cur = db().execute(
                """INSERT INTO trades(market_id,user_id,action,side,shares,collateral,fee,price_after,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (mid, uid, action, side, sh, traded, fee, price_after, now()))
            db().execute("COMMIT")
        except Exception:
            db().execute("ROLLBACK")
            raise

    return {"trade_id": cur.lastrowid, "shares": sh, "collateral": traded, "fee": fee,
            "price_after": round(price_after, 4)}


# ---------------------------------------------------------------- lifecycle

def close_due():
    """Markets past their deadline stop trading. Nothing else changes."""
    n = db().execute("UPDATE markets SET status='closed' WHERE status='open' AND closes_at<=?",
                     (now(),)).rowcount
    return n


def resolve(mid, outcome, evidence, admin_uid):
    """Record the verdict and open the dispute window. No money moves yet."""
    if outcome not in (YES, NO, "VOID"):
        raise MarketError("outcome must be YES, NO or VOID")
    if not (evidence or "").strip():
        raise MarketError("a verdict without evidence is an assertion")
    r = market_row(mid)
    if r["status"] not in ("open", "closed"):
        raise MarketError("this market is already %s" % r["status"])
    db().execute(
        """UPDATE markets SET status='resolved', outcome=?, evidence=?, resolved_at=?, settles_at=?
           WHERE id=?""",
        (outcome, evidence.strip(), now(), now() + core.DISPUTE_WINDOW, mid))
    ledger(admin_uid, None, 0, "resolve:" + outcome, mid)
    return {"market": mid, "outcome": outcome, "settles_at": now() + core.DISPUTE_WINDOW}


def settle(mid):
    """After the dispute window, pay the winners. Idempotent."""
    with core._write_lock:
        db().execute("BEGIN IMMEDIATE")
        try:
            r = market_row(mid)
            if r["status"] == "settled":
                db().execute("COMMIT")
                return {"already": True}
            if r["status"] != "resolved":
                raise MarketError("this market is not resolved")
            if r["settles_at"] and r["settles_at"] > now():
                raise MarketError("the dispute window is still open")
            if db().execute("SELECT 1 FROM disputes WHERE market_id=? AND status='open'",
                            (mid,)).fetchone():
                raise MarketError("an open dispute must be decided first")

            outcome = r["outcome"]
            paid = 0
            for p in db().execute("SELECT * FROM positions WHERE market_id=?", (mid,)):
                if outcome == "VOID":
                    # return what the position cost, capped at what is escrowed
                    amt = max(0, p["cost"])
                else:
                    amt = amm.payout(YES, p["yes_shares"], outcome) + \
                          amm.payout(NO, p["no_shares"], outcome)
                if amt > 0:
                    credit_user(p["user_id"], amt, "settlement", mid)
                    paid += amt
                db().execute("UPDATE positions SET realised=?, yes_shares=0, no_shares=0 WHERE user_id=? AND market_id=?",
                             (amt - p["cost"], p["user_id"], mid))

            account_move("escrow", -paid, "settlement_out", mid)
            # the creator bond comes back on a clean resolution
            if r["created_by"]:
                account_move("escrow", -core.CREATOR_BOND, "bond_release", mid)
                credit_user(r["created_by"], core.CREATOR_BOND, "bond_return", mid)
            db().execute("UPDATE markets SET status='settled' WHERE id=?", (mid,))
            db().execute("COMMIT")
        except Exception:
            db().execute("ROLLBACK")
            raise
    return {"market": mid, "outcome": r["outcome"], "paid": paid}


def open_dispute(uid, mid, reason):
    r = market_row(mid)
    if r["status"] != "resolved":
        raise MarketError("only a resolved market can be disputed")
    if r["settles_at"] and r["settles_at"] <= now():
        raise MarketError("the dispute window has closed")
    if not db().execute("SELECT 1 FROM positions WHERE user_id=? AND market_id=?", (uid, mid)).fetchone():
        raise MarketError("only someone holding a position in this market can dispute it")
    if len((reason or "").strip()) < 20:
        raise MarketError("cite the criterion you believe was misread")
    with core._write_lock:
        db().execute("BEGIN IMMEDIATE")
        try:
            debit_user(uid, core.DISPUTE_BOND, "dispute_bond", mid)
            account_move("escrow", core.DISPUTE_BOND, "dispute_bond", mid)
            cur = db().execute(
                "INSERT INTO disputes(market_id,user_id,reason,bond,created_at) VALUES(?,?,?,?,?)",
                (mid, uid, reason.strip(), core.DISPUTE_BOND, now()))
            db().execute("COMMIT")
        except Exception:
            db().execute("ROLLBACK")
            raise
    return {"dispute_id": cur.lastrowid}


def decide_dispute(did, upheld, new_outcome=None, evidence=None):
    d = db().execute("SELECT * FROM disputes WHERE id=?", (did,)).fetchone()
    if not d:
        raise MarketError("no such dispute")
    if d["status"] != "open":
        raise MarketError("already decided")
    with core._write_lock:
        db().execute("BEGIN IMMEDIATE")
        try:
            if upheld:
                credit_user(d["user_id"], d["bond"], "dispute_bond_return", d["market_id"])
                account_move("escrow", -d["bond"], "dispute_bond_return", d["market_id"])
                if new_outcome:
                    db().execute("UPDATE markets SET outcome=?, evidence=? WHERE id=?",
                                 (new_outcome, evidence or "", d["market_id"]))
            else:
                account_move("escrow", -d["bond"], "dispute_bond_forfeit", d["market_id"])
                account_move("fees", d["bond"], "dispute_bond_forfeit", d["market_id"])
            db().execute("UPDATE disputes SET status=? WHERE id=?",
                         ("upheld" if upheld else "rejected", did))
            db().execute("COMMIT")
        except Exception:
            db().execute("ROLLBACK")
            raise
    return {"dispute": did, "status": "upheld" if upheld else "rejected"}


# ---------------------------------------------------------------- portfolio

def portfolio(uid):
    rows = db().execute(
        """SELECT p.*, m.question, m.category, m.status, m.outcome, m.y_reserve, m.n_reserve
           FROM positions p JOIN markets m ON m.id=p.market_id
           WHERE p.user_id=? AND (p.yes_shares>0 OR p.no_shares>0 OR p.realised<>0)""",
        (uid,)).fetchall()
    out, value = [], 0
    for r in rows:
        p = amm.price_yes(r["y_reserve"], r["n_reserve"])
        mark = int(r["yes_shares"] * p + r["no_shares"] * (1 - p))
        value += mark
        out.append({
            "market": r["market_id"], "question": r["question"], "category": r["category"],
            "status": r["status"], "outcome": r["outcome"],
            "yes_shares": r["yes_shares"], "no_shares": r["no_shares"],
            "cost": r["cost"], "mark": mark, "unrealised": mark - r["cost"],
            "realised": r["realised"], "price": round(p, 4),
        })
    bal = db().execute("SELECT balance FROM users WHERE id=?", (uid,)).fetchone()["balance"]
    return {"balance": bal, "positions": out, "position_value": value, "equity": bal + value}


def leaderboard(limit=20):
    rows = db().execute(
        """SELECT u.handle,
                  COALESCE(SUM(p.realised),0) realised,
                  COUNT(CASE WHEN p.realised<>0 THEN 1 END) resolved,
                  COALESCE(SUM(ABS(p.cost)),0) committed
           FROM users u LEFT JOIN positions p ON p.user_id=u.id
           GROUP BY u.id HAVING resolved > 0
           ORDER BY realised DESC LIMIT ?""", (limit,)).fetchall()
    out = []
    for r in rows:
        roi = (r["realised"] / r["committed"]) if r["committed"] else 0
        out.append({"handle": r["handle"], "realised": r["realised"], "resolved": r["resolved"],
                    "committed": r["committed"], "roi": round(roi, 4)})
    return out
