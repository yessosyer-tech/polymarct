# POLYMARCT — audit and backend build

Date: 2026-09-16. Scope: the whole repo, plus the backend built during this
pass. Method: a static checker (`tools/audit.py`), 61 unit tests on the market
engine, 27 end to end tests over the HTTP API, and a manual pass through every
page in a browser.

---

## 1. The headline finding

Before this pass there was **no backend at all**. Every number on the site came
from a simulation running in the visitor's browser: prices drifted at random,
"positions" existed only until a refresh, and nothing could be resolved, settled
or paid. The site described a market accurately and implemented none of it.

That is now built. What follows is what was found, what was fixed and what is
still genuinely blocking.

---

## 2. Findings, worst first

### BLOCKING, and not fixable in code

**B1. Real money needs legal clearance, not engineering.** Prediction markets
can engage gambling, derivatives, securities and financial promotion regimes at
once, and which ones depends on jurisdiction and market type. Nothing in this
repo should take real funds until that is resolved. Unchanged from
`ARCHITECTURE.md` §6.

**B2. There is no chain integration and no custody.** No contracts, no wallet,
no USDC transfers, no oracle signing. The settlement layer is deliberately
isolated (`server/markets.py: settle`) so it can be swapped for on chain
settlement, but today it settles inside a local database with demo balances.

**B3. The public site cannot run the backend.** GitHub Pages serves static files
only, so `polymarct.xyz` stays in demo mode. The front end detects this and
falls back to the simulation rather than showing broken controls. Running the
real product needs a host that can run a process.

### FIXED in this pass

**F1. The AMM leaked value to traders on every trade.** Found by the test suite,
not by reading. A buy floored the reserve the pool keeps, and a sell floored the
square root in the payout solve. Both rounded the dust toward the trader, so the
constant product invariant shrank a little on every single trade. Over enough
volume that drains the pool. Both now round toward the pool, and the invariant
is asserted on every quote. Tests: "invariant does not shrink on a buy",
"round trip cannot return more than it cost".

**F2. Twelve of the fifty demo markets failed the rules the site publishes.**
The creation validator rejected them: subjective wording ("a major agent interop
standard"), no window stated in the question itself, and one that was not a
yes/no question at all ("Which Arc protocol reaches $100M TVL first?"). The site
was telling visitors that ambiguous questions are rejected while shipping twelve
of them. All twelve rewritten in `assets/js/data.js`; all fifty now pass.

**F3. Renaming a market id broke referential integrity.** The seeder created a
market then renamed it to match the front end, which fails under
`PRAGMA foreign_keys=ON` once positions point at it. Ids are now pinned at
creation instead.

**F4. The seeder silently skipped seven markets.** Its parser broke on the
category comments in `data.js`, so 43 of 50 were imported and nobody would have
noticed. Fixed; the count is now asserted in the seed output.

**F5. A market page fought itself when a server was present.** The simulation
and the server both wrote the price, so the display flickered between them. The
simulation now stands down whenever a server answers.

### OPEN, lower severity

**O1. SQLite, single process.** Correct and safe for demo scale because every
write runs in `BEGIN IMMEDIATE` behind a lock, but it will not survive real
concurrency. Postgres before any public deployment.

**O2. No email verification, no 2FA, no account recovery.** Signup takes an
email and never checks it.

**O3. The faucet is unlimited over time.** Six hour cooldown, no lifetime cap.
Fine for demo money, meaningless as a Sybil control.

**O4. The oracle is a person with a token.** `POLYMARCT_ADMIN_TOKEN` resolves
any market. That is honest for now and matches how most markets actually start,
but it is a single point of trust and the site should not imply otherwise.

**O5. No realtime transport.** The front end polls every six to eight seconds.

**O6. Repo weight is 128 MB** and growing with every asset re-export. Media
should move to a release or a bucket before this becomes painful.

---

## 3. What was built

```
server/amm.py          binary constant product maker, integer only
server/core.py         storage, money, accounts, the append only ledger
server/markets.py      create, trade, close, resolve, settle, dispute
server/app.py          HTTP server, JSON API, static site, rate limits
server/seed.py         imports the 50 markets from assets/js/data.js
server/test_server.py  61 unit tests
server/test_api.py     27 end to end tests over HTTP
assets/js/api.js       front end client, with demo fallback
portfolio.html         balance, positions, P&L and the ledger
```

Endpoints: `/api/health`, `/api/auth/{signup,login,logout}`, `/api/me`,
`/api/faucet`, `/api/markets` (list, detail, create), `/api/quote`,
`/api/trade`, `/api/portfolio`, `/api/ledger`, `/api/leaderboard`,
`/api/dispute`, and `/api/admin/{resolve,settle,dispute,reconcile}`.

### The money model

One share pays exactly one unit if it wins and zero if it loses, so the two
prices always sum to one. Collateral mints one of each outcome; the AMM swaps
the unwanted side out along a constant product curve. All amounts are integer
micro units, so there is no float drift.

Every balance change writes a ledger row. `/api/admin/reconcile` recomputes
every balance from the ledger and reports any disagreement; it is asserted in
the tests after account setup, creation, trading, disputes and settlement.

### Security of the new surface

- Passwords: PBKDF2-HMAC-SHA256, 240,000 rounds, per user salt, constant time
  comparison.
- Sessions: 256 bit tokens, HttpOnly, SameSite=Strict, 14 day expiry, server
  side revocation on logout.
- Writes require `Content-Type: application/json`, which a cross origin form
  post cannot set without CORS, and no CORS origin is allowed.
- Rate limits per IP: 10 auth attempts per 5 minutes, 30 writes per minute,
  120 reads per minute.
- Admin is **closed unless `POLYMARCT_ADMIN_TOKEN` is set**, and the token is
  never stored in the repo.
- Money is integers; `debit_user` refuses to overdraw; trading and settlement
  run inside one transaction each and roll back as a unit.
- Settlement is idempotent, and an open dispute blocks it.
- The static checker found no hardcoded credentials or keys.

### What the tests actually assert

Not "it returned 200". They assert that a buy debits exactly what was spent,
that a round trip cannot return more than it cost, that you cannot sell shares
you do not hold or spend money you do not have, that a closed market refuses
trades, that a verdict without evidence is refused, that the dispute window
blocks settlement, that settlement pays exactly one unit per winning share and
is idempotent, and that the ledger reconciles after every one of those.

---

## 4. Running it

```
python server/seed.py --reset --traders     # 50 markets, 10 demo traders
python server/app.py 8100                   # site and API on one port
python server/test_server.py                # 61 unit tests
python server/test_api.py 8100              # 27 end to end tests
python tools/audit.py                       # static checks
```

Set `POLYMARCT_ADMIN_TOKEN` to enable resolution. `POLYMARCT_FEE_BPS` sets the
protocol fee, default 100 (1%).

---

## 5. What "complete" honestly means here

Every mechanic the site describes now exists and works end to end: accounts,
balances, a real order book with slippage, positions, profit and loss, market
creation under the published rules, closing on the deadline, resolution with
evidence, a bonded dispute window, settlement that pays winners, and a ledger
that explains every unit.

What it does not have is real money, a chain, or a licence. Those are B1 and B2
above, and no amount of code in this repo resolves them.
