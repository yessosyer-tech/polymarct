"""Binary constant product market maker.

One market holds two reserves of outcome shares, YES and NO. Collateral mints
one of each: a dollar buys one YES plus one NO, and exactly one of them is
worth a dollar at settlement, which is why the two prices always sum to one.

    price(YES) = noReserve / (yesReserve + noReserve)

Everything is integers. Money is micro units (1 USDC = 1_000_000) and shares
are micro shares, so there is no float drift and no dust that cannot be
accounted for. Rounding always favours the pool, never the trader, so the
invariant can only grow.
"""
import math

MICRO = 1_000_000          # one unit, in micro units
YES, NO = "YES", "NO"


class AmmError(Exception):
    pass


def price_yes(y, n):
    """Probability of YES, as a float in (0,1). Display only, never money."""
    if y <= 0 or n <= 0:
        raise AmmError("empty reserves")
    return n / (y + n)


def quote_buy(y, n, side, collateral, fee_bps):
    """Spend `collateral` micro USDC on `side`. Returns (shares, fee, y2, n2).

    The pool mints the spend into one of each outcome, then swaps the unwanted
    side out along the curve.
    """
    if collateral <= 0:
        raise AmmError("amount must be positive")
    if side not in (YES, NO):
        raise AmmError("side must be YES or NO")
    fee = collateral * fee_bps // 10_000
    c = collateral - fee
    if c <= 0:
        raise AmmError("amount too small to cover the fee")

    k = y * n
    y1, n1 = y + c, n + c
    # ceiling on the reserve the pool keeps, so the product can only grow and
    # the rounding dust stays with the pool rather than with the trader
    if side == YES:
        keep = -(-k // n1)
        shares = y1 - keep
        y2, n2 = keep, n1
    else:
        keep = -(-k // y1)
        shares = n1 - keep
        y2, n2 = y1, keep

    if shares <= 0:
        raise AmmError("amount too small to move the book")
    if y2 * n2 < k:
        raise AmmError("invariant would shrink")
    return shares, fee, y2, n2


def quote_sell(y, n, side, shares, fee_bps):
    """Return `shares` of `side` to the pool. Returns (payout, fee, y2, n2).

    Solves (A - x)(B - x) = k for the collateral x that can be burned back out,
    where A is the reserve the shares are added to and B is the other one.
    """
    if shares <= 0:
        raise AmmError("shares must be positive")
    if side not in (YES, NO):
        raise AmmError("side must be YES or NO")

    k = y * n
    if side == YES:
        a, b = y + shares, n
    else:
        a, b = n + shares, y

    s = a + b
    disc = s * s - 4 * (a * b - k)
    if disc < 0:
        raise AmmError("no solution, reserves inconsistent")
    # round the root UP so the payout is rounded DOWN. Flooring the square root
    # would bias x upward and hand the rounding dust to the trader, which over
    # many trades drains the pool one micro unit at a time.
    r = math.isqrt(disc)
    if r * r < disc:
        r += 1
    x = (s - r) // 2
    if x <= 0:
        raise AmmError("position too small to sell")

    if side == YES:
        y2, n2 = a - x, b - x
    else:
        y2, n2 = b - x, a - x
    if y2 <= 0 or n2 <= 0:
        raise AmmError("sale would empty the pool")
    if y2 * n2 < k:
        raise AmmError("invariant would shrink")

    fee = x * fee_bps // 10_000
    return x - fee, fee, y2, n2


def seed(collateral):
    """Open a book at even odds. Minting gives one of each outcome."""
    if collateral <= 0:
        raise AmmError("seed must be positive")
    return collateral, collateral


def open_at(collateral, target_price, fee_bps=0):
    """Seed a book, then move it to `target_price` by taking the other side.

    Returns (y, n, side_held, shares_held, spent). The mover ends up holding a
    real position, because there is no way to start a market away from even
    odds without somebody actually being on one side of it.
    """
    if not 0.01 <= target_price <= 0.99:
        raise AmmError("target price out of range")
    y, n = seed(collateral)
    side = YES if target_price > 0.5 else NO
    lo, hi = 0, collateral * 40
    best = None
    for _ in range(60):                     # bisect on spend, prices are monotone
        mid = (lo + hi) // 2
        if mid <= 0:
            break
        try:
            sh, fee, y2, n2 = quote_buy(y, n, side, mid, fee_bps)
        except AmmError:
            lo = mid + 1
            continue
        p = price_yes(y2, n2)
        if (side == YES and p < target_price) or (side == NO and p > target_price):
            lo = mid + 1
        else:
            hi = mid - 1
        best = (sh, fee, y2, n2, mid)
    if not best:
        raise AmmError("could not open at that price")
    sh, fee, y2, n2, spent = best
    return y2, n2, side, sh, spent


def payout(side, shares, outcome):
    """At settlement a winning share is worth exactly one unit, a loser zero."""
    if outcome not in (YES, NO, "VOID"):
        raise AmmError("bad outcome")
    if outcome == "VOID":
        return 0
    return shares if side == outcome else 0
