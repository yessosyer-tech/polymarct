# POLYMARCT

**THE LEADING PREDICTION MARKET ON ARC.**
The #1 market for what happens next.

Static build, no toolchain. Open `index.html` in a browser, or serve the folder.

```bash
python -m http.server 8080
```

---

## Pages

| File | What it is |
|---|---|
| `index.html` | Hero + live market field, live grid, Signal, Against the Crowd, Arc // Live, Future Index, What the World Thinks, Daily Brief, $PMARC, CTA |
| `markets.html` | Full board: category filters, search, sorts (moving / volume / new / closing / early / contrarian) |
| `market.html?m=<id>` | Market detail: huge probability, trade panel, hover chart, intelligence, why it is moving, live trades, resolution, terminal depth + history, connected markets |
| `discover.html` | The feed: Moving Now, Early Signals, Whale Activity, Breaking, Against the Crowd, New, What the World Thinks |
| `signals.html` | THE SIGNAL: filterable live event stream + pulse stats |
| `map.html` | THE MARKET MAP: force directed graph, pan / zoom / hover / click through |
| `arc.html` | ARC // LIVE: network telemetry, protocol ranking, ecosystem markets |
| `leaderboard.html` | THE CONVICTION INDEX, with the anti gaming method stated |
| `token.html` | $PMARC: the asset, the animated mark, why it exists, what is not claimed |
| `create.html` | Market creation with an 8 point validation gate and live preview |
| `verdict.html` | The Verdict Engine, dispute flow, trust guarantees, risk and eligibility |
| `404.html` | "This market doesn't exist. Yet." |
| `brand/index.html` | Brand system: the mark, construction, the three films, colour and type |
| `brand/studio.html` | Content Studio: six export formats rendered from live market state, one click PNG |
| `brand/motion/00-trailer.html` | **Trailer**, 30s, 60 cuts, synthesised score, voice-over |
| `brand/motion/01-ident.html` | Motion 01, IDENT, 15s |
| `brand/motion/02-flow.html` | Motion 02, THE FLOW, 26s |
| `brand/motion/03-network.html` | Motion 03, THE NETWORK, 24s |

## Code

- `assets/css/polymarct.css` — the whole design system
- `assets/js/data.js` — 50 markets across 7 categories, each with resolution criteria and a named source; Arc telemetry, protocols, traders, themes
- `assets/js/engine.js` — seeded history, live tick loop, momentum, EARLY, contrarian score, Future Index, theme aggregates, drivers
- `assets/js/ui.js` — header, footer, market card, sparkline, ticker, modals, toasts, terminal mode
- `assets/js/field.js` — the hero live market field canvas

## The backend

With the server running, the site is a working market rather than a picture of
one: accounts, a real book with slippage, positions, P&L, creation under the
published rules, resolution with evidence, a bonded dispute window, settlement,
and a ledger that explains every unit. Balances are demo USDC from a faucet.

```bash
python server/seed.py --reset --traders   # 50 markets, 10 demo traders
python server/app.py 8100                 # site and API on one port
python server/test_server.py              # 61 unit tests
python server/test_api.py 8100            # 28 end to end tests
python tools/audit.py                     # static audit
```

Set `POLYMARCT_ADMIN_TOKEN` to enable resolution; without it the admin routes
are closed. The static host cannot run a process, so `polymarct.xyz` stays in
demo mode and the front end falls back to the browser simulation. Findings and
open items are in `AUDIT.md`.

## PNG is the house format

Every image asset ships as PNG, and that is the standing rule for anything added later: icons, marks, lockups, wordmarks, the link preview and the whole social pack. PNG opens anywhere, holds the acid exactly and needs no renderer. The SVG set stays in `brand/logo/` for print and for the web, but nothing on the site depends on it.

- `brand/logo/png/` — mark at 16 to 1024 transparent, on graphite and on warm white, one colour versions, lockups and wordmarks. Rebuild with `/brand/export-logo.html` and `LOGOS.all()`.
- `assets/icons/` — favicon 16/32/48, apple touch 180, 192 and 512. Declared on every page.
- `assets/og-image.png` — 1200x630 link preview, wired as `og:image` and `twitter:image`.
- `png/` — **the deliverable tree**, see below.

## png/ is the deliverable

Everything that gets handed over is a PNG in a numbered folder. No page to open, no renderer to run.

| Folder | Files | What it is |
|---|---|---|
| `00-contact-sheets` | 6 | One sheet per folder, every image at a glance |
| `01-logo` | 30 | Mark 16 to 1024, transparent, on graphite, on warm white, one colour, lockups, wordmarks |
| `02-icons` | 6 | Favicon 16/32/48, apple touch 180, 192, 512 |
| `03-social` | 36 | Signal, hook, explainer, stat and portrait cards, plus `POSTING-PLAN.txt` |
| `04-profile` | 2 | X header 1500x500, avatar 400x400 |
| `05-link-preview` | 1 | og-image 1200x630 |
| `06-film-stills` | 28 | Frames from the four films, 1920x1080 |

Rebuild the tree with `python tools/build_png.py`. Regenerate the source art first if the markets should be fresh: serve the site, open the exporters, run `LOGOS.all()` and `EXPORT.all()`.

## Video files

Finished MP4s live in `dist/`: the trailer at 1080p60 with its score, plus vertical, square and a small share cut, and the three product films at 1080p30, silent.

They are not screen recordings. `tools/serve.py` serves the site and accepts POSTed frames; `brand/motion/render.js` seeks each film to an exact time, reads the canvas and posts the frame, and `brand/motion/baker.js` paints the films DOM type onto that canvas so nothing is missing. The score is rendered through an OfflineAudioContext, so it is sample exact. ffmpeg muxes the result. Every run is identical.

## The asset rule

USDC on Arc is the only asset the product accepts: collateral, trades, fees, bonds and payouts. No ETH, no second token, no other chain, no card, no swap, no bridge-in. $PMARC is not a payment asset and is never needed to trade. See `ARCHITECTURE.md` section 0.1.

## Brand

The mark is **the book**: two sides of the order book facing each other, the taller bracket holding the weight of the money, the shorter one the other outcome, and the acid bar standing in the gap between them as the last price. Acid is the price and never a field. It animates by repricing itself. Logo pack in `brand/logo/`, geometry mirrored in `assets/js/ui.js`, `brand/brand-render.js` and `brand/motion/motion.js`.

The 30 second trailer cuts on a 120 BPM grid with a score synthesised in the page and a voice-over on timed cues; drop `brand/motion/audio/vo.mp3` in and a real recording takes over from the browser scratch voice. Script and timecodes in `brand/motion/TRAILER-VO.md`. The three product films run on a deterministic timeline at 1920x1080, so a screen recording is repeatable rather than a lucky take. Add `?rec=1` for a clean plate, `&t=6` to seek, `&pause=1` to hold a frame.

## Design

Near black graphite, warm white, acidic electric green (`#CCFF00`), electric blue secondary. Hairlines, 2px radii, tabular numbers, huge tight tracked headlines, small uppercase mono metadata. No purple gradients, no glassmorphism, no rounded pill soup. Motion carries information only: probabilities tick, cards flash on the direction of the move, the chart breathes, the field drifts. `prefers-reduced-motion` stops the simulation loop and the field.

Terminal mode is a real mode, not a skin: header toggle, persisted in `localStorage`, denser grid, and it reveals market depth and trade history on the detail page.

## Status

Demonstration state. Every number is generated in the browser: no wallet, no orders, no settlement, no funds. See `ARCHITECTURE.md` for the contract, oracle, indexer and compliance layers that have to exist before a real money launch.
