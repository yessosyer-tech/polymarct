"""Storage, money and accounts.

SQLite, integers only, and an append only ledger. Every balance change in the
system is a ledger row: if a balance moved and there is no row explaining it,
that is a bug, and the reconcile check will say so.

Balances are demo USDC. Nothing here touches a chain or real funds; the
settlement layer is deliberately isolated so it can be replaced by on chain
settlement without moving anything else.
"""
import os
import re
import json
import time
import hmac
import hashlib
import secrets
import sqlite3
import threading

from amm import MICRO, YES, NO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("POLYMARCT_DB", os.path.join(ROOT, "server", "polymarct.db"))

FEE_BPS = int(os.environ.get("POLYMARCT_FEE_BPS", "100"))        # 1.00% on the collateral leg
FAUCET = 1_000 * MICRO                                           # demo top up
FAUCET_COOLDOWN = 6 * 3600
SESSION_TTL = 14 * 24 * 3600
PBKDF_ROUNDS = 240_000
CREATOR_BOND = 500 * MICRO
MIN_SEED = 500 * MICRO
DISPUTE_BOND = 100 * MICRO
DISPUTE_WINDOW = 24 * 3600

HOUSE = "house"                                                  # the protocol liquidity account

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  handle TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  pw_salt TEXT NOT NULL,
  pw_hash TEXT NOT NULL,
  balance INTEGER NOT NULL DEFAULT 0,
  is_admin INTEGER NOT NULL DEFAULT 0,
  faucet_at INTEGER NOT NULL DEFAULT 0,
  created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS markets (
  id TEXT PRIMARY KEY,
  question TEXT NOT NULL,
  category TEXT NOT NULL,
  criteria TEXT NOT NULL,
  source TEXT NOT NULL,
  closes_at INTEGER NOT NULL,
  created_by INTEGER REFERENCES users(id),
  created_at INTEGER NOT NULL,
  y_reserve INTEGER NOT NULL,
  n_reserve INTEGER NOT NULL,
  seed INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',      -- open | closed | resolved | void
  outcome TEXT,
  evidence TEXT,
  resolved_at INTEGER,
  settles_at INTEGER,
  spec_hash TEXT NOT NULL,
  volume INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS positions (
  user_id INTEGER NOT NULL REFERENCES users(id),
  market_id TEXT NOT NULL REFERENCES markets(id),
  yes_shares INTEGER NOT NULL DEFAULT 0,
  no_shares INTEGER NOT NULL DEFAULT 0,
  cost INTEGER NOT NULL DEFAULT 0,          -- net collateral committed, for P&L
  realised INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, market_id)
);
CREATE TABLE IF NOT EXISTS trades (
  id INTEGER PRIMARY KEY,
  market_id TEXT NOT NULL REFERENCES markets(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  action TEXT NOT NULL,                     -- buy | sell
  side TEXT NOT NULL,                       -- YES | NO
  shares INTEGER NOT NULL,
  collateral INTEGER NOT NULL,
  fee INTEGER NOT NULL,
  price_after REAL NOT NULL,
  created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS ledger (
  id INTEGER PRIMARY KEY,
  user_id INTEGER,
  account TEXT,
  delta INTEGER NOT NULL,
  reason TEXT NOT NULL,
  ref TEXT,
  created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS disputes (
  id INTEGER PRIMARY KEY,
  market_id TEXT NOT NULL REFERENCES markets(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  reason TEXT NOT NULL,
  bond INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',      -- open | upheld | rejected
  created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS accounts (
  name TEXT PRIMARY KEY,
  balance INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_trades_market ON trades(market_id, id DESC);
CREATE INDEX IF NOT EXISTS idx_ledger_user ON ledger(user_id, id DESC);
CREATE INDEX IF NOT EXISTS idx_markets_status ON markets(status, closes_at);
"""

_local = threading.local()
_write_lock = threading.Lock()


def db():
    if not getattr(_local, "conn", None):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        c = sqlite3.connect(DB_PATH, timeout=20, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA busy_timeout=8000")
        _local.conn = c
    return _local.conn


def init():
    c = db()
    c.executescript(SCHEMA)
    c.execute("INSERT OR IGNORE INTO accounts(name,balance) VALUES(?,0)", (HOUSE,))
    c.execute("INSERT OR IGNORE INTO accounts(name,balance) VALUES('fees',0)")
    c.execute("INSERT OR IGNORE INTO accounts(name,balance) VALUES('escrow',0)")
    return c


def now():
    return int(time.time())


# ---------------------------------------------------------------- money

def ledger(user_id, account, delta, reason, ref=None):
    db().execute(
        "INSERT INTO ledger(user_id,account,delta,reason,ref,created_at) VALUES(?,?,?,?,?,?)",
        (user_id, account, delta, reason, ref, now()))


def credit_user(uid, amount, reason, ref=None):
    if amount == 0:
        return
    db().execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, uid))
    ledger(uid, None, amount, reason, ref)


def debit_user(uid, amount, reason, ref=None):
    if amount <= 0:
        return
    row = db().execute("SELECT balance FROM users WHERE id=?", (uid,)).fetchone()
    if not row or row["balance"] < amount:
        raise ValueError("insufficient balance")
    db().execute("UPDATE users SET balance = balance - ? WHERE id=?", (amount, uid))
    ledger(uid, None, -amount, reason, ref)


def account_move(name, delta, reason, ref=None):
    db().execute("UPDATE accounts SET balance = balance + ? WHERE name=?", (delta, name))
    ledger(None, name, delta, reason, ref)


def reconcile():
    """Every balance must equal the sum of its ledger rows. No exceptions."""
    c = db()
    bad = []
    for u in c.execute("SELECT id,balance FROM users"):
        s = c.execute("SELECT COALESCE(SUM(delta),0) d FROM ledger WHERE user_id=?", (u["id"],)).fetchone()["d"]
        if s != u["balance"]:
            bad.append("user %d balance %d != ledger %d" % (u["id"], u["balance"], s))
    for a in c.execute("SELECT name,balance FROM accounts"):
        s = c.execute("SELECT COALESCE(SUM(delta),0) d FROM ledger WHERE account=?", (a["name"],)).fetchone()["d"]
        if s != a["balance"]:
            bad.append("account %s balance %d != ledger %d" % (a["name"], a["balance"], s))
    return bad


# ---------------------------------------------------------------- accounts

HANDLE_RE = re.compile(r"^[a-zA-Z0-9_]{3,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF_ROUNDS)
    return salt, h.hex()


def check_password(password, salt, expected):
    _, h = hash_password(password, salt)
    return hmac.compare_digest(h, expected)


def create_user(handle, email, password, is_admin=0):
    if not HANDLE_RE.match(handle or ""):
        raise ValueError("handle must be 3 to 20 letters, numbers or underscores")
    if not EMAIL_RE.match(email or ""):
        raise ValueError("that email does not look like an email")
    if not password or len(password) < 10:
        raise ValueError("password must be at least 10 characters")
    salt, h = hash_password(password)
    try:
        cur = db().execute(
            "INSERT INTO users(handle,email,pw_salt,pw_hash,balance,is_admin,created_at) VALUES(?,?,?,?,0,?,?)",
            (handle, email.lower(), salt, h, is_admin, now()))
    except sqlite3.IntegrityError:
        raise ValueError("that handle or email is already taken")
    return cur.lastrowid


def login(email, password):
    row = db().execute("SELECT * FROM users WHERE email=?", ((email or "").lower(),)).fetchone()
    if not row or not check_password(password or "", row["pw_salt"], row["pw_hash"]):
        return None
    return row["id"]


def new_session(uid):
    token = secrets.token_urlsafe(32)
    db().execute("INSERT INTO sessions(token,user_id,created_at,expires_at) VALUES(?,?,?,?)",
                 (token, uid, now(), now() + SESSION_TTL))
    return token


def user_for_token(token):
    if not token:
        return None
    row = db().execute(
        "SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=? AND s.expires_at>?",
        (token, now())).fetchone()
    return row


def drop_session(token):
    db().execute("DELETE FROM sessions WHERE token=?", (token,))


def faucet(uid):
    row = db().execute("SELECT faucet_at FROM users WHERE id=?", (uid,)).fetchone()
    if row and now() - row["faucet_at"] < FAUCET_COOLDOWN:
        wait = FAUCET_COOLDOWN - (now() - row["faucet_at"])
        raise ValueError("faucet again in %d minutes" % (wait // 60))
    credit_user(uid, FAUCET, "faucet")
    db().execute("UPDATE users SET faucet_at=? WHERE id=?", (now(), uid))
    return FAUCET


def spec_hash(question, criteria, source, closes_at):
    """What the market promised, hashed at creation. It cannot change after."""
    blob = json.dumps({"q": question, "c": criteria, "s": source, "t": closes_at},
                      sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()
