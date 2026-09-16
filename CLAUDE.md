# POLYMARCT — project context for Claude

Read this before touching anything. It is the whole brief in one file.

## 1. What this is

**Polymarct** ($PMARC) is a prediction market for the **Arc** chain. Users trade
YES/NO on real questions; the price is the probability. Positioned as a serious
information market, not a betting app: "the Bloomberg of prediction markets".

- **Live:** https://polymarct.xyz (GitHub Pages, repo `yessosyer-tech/polymarct`,
  custom domain, HTTPS enforced, `www` redirects to apex)
- **Deploy:** `git push` to `main`. That is the whole pipeline.
- **Local:** `python tools/serve.py` then http://localhost:8099

**Everything on the site is demonstration state.** No wallet, no orders, no
settlement, no funds. Market numbers are generated in the browser by a
simulation. Never present it as live trading.

## 2. Stack

Static vanilla HTML/CSS/JS. **No build step, no framework, no Node.** Python 3
and ffmpeg are available locally; Node is not. Do not introduce a toolchain.

```
index.html markets.html market.html discover.html signals.html map.html
arc.html leaderboard.html token.html create.html verdict.html 404.html
assets/css/polymarct.css      the entire design system
assets/js/data.js             50 markets, each with resolution criteria + named source
assets/js/engine.js           seeded history, live tick sim, momentum, Future Index
assets/js/ui.js               header, footer, cards, ticker, modals, terminal mode
assets/js/field.js            hero canvas
brand/                        exporters and the motion films (machinery, not deliverables)
tools/serve.py                dev server, also accepts POSTed frames at /_save/<name>
tools/build_png.py            builds the png/ deliverable tree
png/                          THE DELIVERABLE: every asset as PNG in numbered folders
dist/                         four finished MP4 films
ARCHITECTURE.md               what must exist before real money (contracts, oracle, compliance)
```

## 3. Hard rules — do not break these

**USDC on Arc is the only asset the product accepts.** Collateral, trades, fees,
bonds, payouts. No ETH, no second token, no other chain, no card, no swap, no
bridge-in. $PMARC is **not** a payment asset and is never needed to trade. This
is enforced in copy everywhere and specified in `ARCHITECTURE.md` §0.1.

**No financial promises.** No guaranteed returns, no "risk free", no APY, no
yield, no price predictions of our own. Not in copy, not in an image, not in a
caption. The design can be aggressive; the claims cannot.

**Product first, token second.** $PMARC never leads. If the token is the hook,
the account reads as a token account.

**Deliverables are PNG files in folders. Never hand over HTML.** The website is
HTML because it is a website, and `brand/*.html` are the exporters that draw the
PNGs, but neither is ever presented as a result. The handover is `png/`.

**The domain is not on the assets yet.** `brand/brand-render.js` has a `SIG`
constant (currently `$PMARC // ON ARC`). Flip it to the domain only when asked;
it changes every card and needs a re-export.

## 4. Design law

- Near-black graphite `#08090A`, warm white `#F2EFE9`, **acid `#CCFF00`**,
  electric blue `#2F6BFF` secondary, signal red `#FF4D2E`.
- **Acid is the price. Never a field, never a background.** This rule killed two
  earlier logos; it is not negotiable.
- Inter Tight for headlines, tight tracking, huge. JetBrains Mono for every
  number and label, tabular figures. The numbers are the design objects.
- Hairlines, 2px radii. **No** purple gradients, no glassmorphism, no rounded
  pill soup, no stock imagery, no AI-generated pictures.
- Motion only where it carries information. No bounce, no spin, no particles.
- Copy voice: flat, certain, no exclamation marks, no em dashes, no " · "
  separators. Use `//` as the separator. Microcopy is TAKE YES / TAKE NO /
  ENTER MARKET / POSITION CONFIRMED / THE VERDICT IS IN.
- **Nothing is drawn behind type.** Background texture under a headline is what
  caused a rejected batch. Keep the ground empty and use structure.

## 5. The logo — THE BOOK

Two sides of the order book facing each other. The taller bracket is the side
holding the weight of the money, the shorter one is the other outcome, and the
**acid bar in the gap is the last price**.

Geometry is duplicated in five places and they must stay in sync:
`brand/logo/*.svg`, `brand/logo/png/*`, the `GLYPH` in `assets/js/ui.js`,
`mark()` in `brand/brand-render.js`, `drawMark()` in `brand/motion/motion.js`.
Change it in one place and regenerate; do not hand-edit five copies.

## 6. Asset pipelines

All exporters run in the browser against `tools/serve.py`, which writes POSTed
files to `tools/out/`.

| Asset | Page | Call |
|---|---|---|
| Logo, icons, og-image | `/brand/export-logo.html` | `LOGOS.all()` |
| Social pack | `/brand/export.html` | `EXPORT.all()` |
| Twitter set (10 explainers) | `/brand/export-twitter.html` | `TW.all()`, and `TW.collisions()` must say clean for all ten |
| Films → frames | `/brand/motion/0X-*.html?rec=1&pause=1` | `RENDER.run({fps:30})` |

Then `python tools/build_png.py` assembles `png/` and the contact sheets.
Compress big PNGs with Pillow `quantize(256)`; it cuts ~60% with no visible loss.

`build_png.py` distinguishes **derived** folders (01, 02, 05, 06, contact sheets;
rebuilt every run) from **authored** ones (03-social, 04-profile, Twitter; the
files live there and nowhere else). Never wipe an authored folder.

## 7. Gotchas that cost hours

- **rAF freezes when the browser pane is hidden**, so realtime `MediaRecorder`
  capture is useless. Films are rendered frame by frame instead.
- `SimpleHTTPRequestHandler` needs `protocol_version = "HTTP/1.1"` or ~1800
  rapid POSTs exhaust the socket table mid-render.
- In `brand/motion/baker.js`, `fontSize` / `letterSpacing` / border widths are
  already in stage space but `getBoundingClientRect` is not. Bake with the stage
  at `transform:none`.
- The motion `Timeline` applies **only beats that have started**, with a per-film
  `reset()`. Earlier, beats writing their `p=0` state silently overwrote
  everything downstream.
- Films 01–03 draw type in the DOM, which a canvas capture cannot see. That is
  what `baker.js` is for.

## 8. What is NOT built

No contracts, no AMM, no orderbook, no oracle, no indexer, no wallet connection,
no compliance gating. `ARCHITECTURE.md` specifies all of it, including the
jurisdiction/KYC work that must exist before real money. Do not imply any of it
is running.

## 9. Working alongside someone else

- Branch per person, PR into `main`. Pages deploys from `main`, so anything
  merged is instantly public.
- Coordinate before touching `assets/js/ui.js`, `assets/css/polymarct.css` or
  `brand/brand-render.js` — everything depends on them.
- Regenerating any asset pack rewrites many binaries at once and will conflict
  ugly. Agree who owns a pack before re-exporting it.
- `dist/` and `png/` are committed binaries. Do not rebase or force-push them.

## 10. Open items

- Flip `SIG` and add absolute `og:url` when the domain should appear on assets.
- Films 01–03 are silent; the trailer has a synthesised score.
- The trailer voice-over is a browser scratch track. Dropping a real recording
  at `brand/motion/audio/vo.mp3` takes over automatically; script with timecodes
  is in `brand/motion/TRAILER-VO.md`.
- More markets: `data.js` has 50, the launch brief asks for 70+.
