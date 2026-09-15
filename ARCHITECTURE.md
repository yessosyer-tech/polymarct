# POLYMARCT // SYSTEM ARCHITECTURE

This file covers brief sections 48, 49 and 50: what has to exist behind the
site before a single real dollar moves. The site in this repo is the
experience layer. Everything below is the part that makes it a market.

---

## 0. What exists today vs what does not

| Layer | Status |
|---|---|
| Brand, copy system, visual language | built |
| Market experience (discover, card, detail, map, signal, terminal) | built, demo state |
| Market creation with validation gate | built, client side only |
| Wallet connection | not built |
| AMM / orderbook, settlement contracts | not built |
| Verdict Engine (oracle + dispute) | specified, not built |
| Indexer, real time feed | not built (simulated in `engine.js`) |
| Compliance: jurisdiction gating, KYC, age | not built |

Nothing in this build touches funds. Every number is generated in the browser.

---

## 1. Chain layer (Arc)

Arc is the right base for this product for three concrete reasons, not because
it is new:

1. **USDC denominated fees.** A market that reprices hundreds of times a day
   cannot pay volatile gas in a volatile asset, and a trader cannot price a
   1 cent edge against an unpredictable fee.
2. **Stablecoin native settlement.** The unit of account for a probability
   market must be the unit the payout is in. No wrapping, no basis risk.
3. **Fast deterministic finality.** Resolution and settlement must not be
   reorg sensitive. "Settled" has to mean settled.

Contracts:

- `MarketFactory` — deploys a market from a validated question spec. Stores the
  spec hash on chain at creation so wording is immutable.
- `Market` — holds YES/NO outcome positions, collateral, fee accounting.
- `AMM` (phase 1) — constant product over binary outcome shares with a fee
  taken on the trade, plus an LP share token. Simple, always quotes, survives
  thin markets.
- `OrderBook` (phase 2) — for high volume markets where an AMM leaks to
  arbitrage. AMM stays as a backstop quote.
- `Settlement` — pays 1 USDC per winning share after the dispute window.
- `VerdictEngine` — see section 3.
- `Treasury` — protocol fee accrual, LP rewards, creator deposit escrow.

Positions are ERC-1155 (one id per outcome per market) so a portfolio is one
balance query and secondary transfer is free.

---

## 2. Pricing and liquidity

**Phase 1: binary CPMM.** Reserves of YES and NO shares; price of YES is
`noReserve / (yesReserve + noReserve)`, which is directly readable as a
probability. Fee on each trade, split between LPs and treasury.

**Seeded liquidity.** Every market opens with a creator seed (minimum 500
USDC in the create flow). A market with no book is not a market, it is a poll.

**Liquidity incentives.** Rewards weight *quote uptime on resolved markets*,
not notional. Rewarding notional pays wash traders.

**Thin market protection.** Max position size scales with liquidity. Slippage
warnings appear before the trade, not after.

---

## 3. The Verdict Engine

Flow: `event → source read → verification → resolution → dispute window → settlement`

- **Pre commitment.** Source, criteria and resolution time are fixed at
  creation and hashed on chain. The question cannot change after trading opens.
  This is the single most important rule in the system.
- **Primary + declared fallback.** Two sources named at creation, never
  improvised at resolution time.
- **Evidence published.** The raw reading that produced the verdict is stored
  with the verdict. A verdict without evidence is an assertion.
- **Dispute window.** 24 hours, bonded, open to any position holder, argued
  only against the original wording.
- **Void path.** If the source is discontinued and the fallback cannot answer,
  the market voids and positions return at cost. A wrong verdict is worse than
  no verdict.

Resolution sources are admissible only from a governed list (price feeds,
official filings, primary publications). Social platforms are never a source.

---

## 4. Off chain services

- **Indexer** — consumes Arc blocks, maintains market state, positions,
  trades, volume, liquidity, holder counts. Source of truth for all reads.
- **Realtime gateway** — websocket fanout of price ticks, trades, liquidity
  events. The browser shape is already what `engine.js` simulates, so the
  swap is a transport change, not a rewrite.
- **Signal service** — computes momentum, EARLY, contrarian score, information
  events, the Future Index and theme aggregates. Deterministic, recomputed per
  tick, never a black box shown to the user as a mystery number.
- **Notification service** — market moved, position resolved, dispute opened,
  settlement ready.
- **Market Map graph builder** — edges from shared tags, assets, events and
  realised correlation between probability series.
- **Artifact renderer** — server side render of the share card per market for
  the social loop (market → artifact → social → user → market).

---

## 5. Security controls

- Contract audits before any mainnet value, plus a public test period.
- Rate limits and per address position caps at launch.
- Oracle key separation: the account that publishes verdicts never holds
  settlement funds.
- Circuit breaker: halt trading on a market whose source feed goes stale, and
  say so on the market page rather than quietly quoting into the void.
- Sybil and wash detection on the Conviction Index (funding graph clustering,
  self matched flow discarded).
- Full incident visibility. Surface failures in the interface. A silent
  failure in a market product is a loss of trust that does not come back.

---

## 6. Compliance (blocking, not optional)

Do not launch the real money product on the strength of a website concept.
Depending on jurisdiction and market type, prediction markets can engage
gambling, derivatives, securities and financial promotion regimes at once.

Build into the architecture, not bolted on after:

- jurisdiction gating at the edge, with category level restriction
- age restriction
- KYC / AML where required, tiered by activity
- risk disclosure at first trade, not buried in a footer
- market category allowlist per jurisdiction
- records and reporting hooks

Marketing constraints that apply to every surface:

- no promised or implied return, no "risk free", no fabricated APY
- $PMARC is an ecosystem asset, never marketed as an investment
- probabilities are the market's price, never presented as Polymarct's forecast

The visual design can be aggressive. The financial claims cannot.

---

## 7. Build order

1. Contracts: `MarketFactory`, `Market`, CPMM, `Settlement`, on testnet.
2. Indexer + realtime gateway, replacing `engine.js` with the same state shape.
3. Wallet connect, USDC deposit, one real market end to end on testnet.
4. Verdict Engine with two sources and the dispute window.
5. Compliance gating, then a closed beta with capped position sizes.
6. Audit, public test period, then mainnet with a small number of markets that
   each have a credible source and real information value.
