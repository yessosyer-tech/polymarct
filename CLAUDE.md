# POLYMARCT — project context for Claude

Read this before touching anything. It is the whole brief in one file.

## 1. What this is

**Polymarct** ($PMARC) is a prediction market for the **Arc** chain. Users trade
YES/NO on real questions; the price is the probability. Positioned as a serious
information market, not a betting app: "the Bloomberg of prediction markets".

- **Live:** https://polymarct.xyz (GitHub Pages, repo `yessosyer-tech/polymarct`,
  custom domain, HTTPS enforced, `www` redirects to apex)
- **Deploy:** `git push` to `main`. That is the whole pipeline.
- **Local, full product:** `python server/seed.py --reset --traders` then
  `python server/app.py 8100`
- **Local, static only:** `python tools/serve.py` then http://localhost:8099

**Two modes.** With `server/app.py` running the site is a working market:
accounts, a real constant product book with slippage, positions, P&L, market
creation, resolution, a bonded dispute window and settlement, all recorded in
SQLite with an append only ledger. Without it, the front end falls back to the
browser simulation, which is what the public static host runs.

**Balances are demo USDC from a faucet.** No wallet, no chain, no custody, no
real funds anywhere. Never present it as live trading. See `AUDIT.md`.

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
server/amm.py                 binary constant product maker, integer money
server/core.py                storage, accounts, the append only ledger
server/markets.py             create, trade, close, resolve, settle, dispute
server/app.py                 HTTP server, JSON API, static site, rate limits
server/seed.py                imports the 50 markets from assets/js/data.js
server/test_server.py         61 unit tests    python server/test_server.py
server/test_api.py            28 API tests     python server/test_api.py 8100
assets/js/api.js              front end client, falls back to the simulation
tools/audit.py                static audit     python tools/audit.py
tools/serve.py                static dev server, accepts POSTed frames at /_save/<name>
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

## 5b. The mascot — TICK

TICK is the acid bar from the mark, stood up and given a face. A tick is the
smallest move a price can make, and in the logo that bar **is** the last price
sitting in the gap between the two sides of the book.

At the end of his film he climbs back into that gap and becomes the bar. That
shot is the mascot's whole argument, do not cut it.

**He is Python, not a browser.** One module draws him everywhere:

    tools/tick.py    tick.draw(img, x, y, s, pose, dir, expr, label, t) -> hand
                     tick.pointer(img, hand, target)
    tools/tick_cards.py   the four explainer cards and the character sheet
    tools/tick_film.py    the 24s film straight to MP4 (Pillow frames, a stdlib
                          `wave` synth for the score, ffmpeg to mux)

An earlier TICK lived in `brand/mascot.js` and was rendered through HTML pages.
The operator called that version too simple and banned the HTML route outright,
so the JS mascot, its sheet page, its exporter and `brand/motion/05-tick.html`
are deleted. Do not bring them back.

Never redraw him by hand. Rules that do not change: body acid, visor graphite,
eyes and arms warm white, the data dot on his price tape electric blue, nothing
else. He floats, because a price does not walk. He never covers the number he
points at, and he points with the dashed acid line, never a drawn arrow. Poses:
idle, point, think, cheer, hold, press, confused. Faces: neutral, happy, focus,
wide, confused. His bounding box is registered in the collision checker, which
is how we caught him standing on a paragraph.

He explains, he does not sell. No exclamation marks, no predictions of his own.
His opening line, in the tour film and on the first content card, is "I am TICK."

**Never mock up the product.** `tools/shots.py` drives headless Chrome over a
local server and writes one tall PNG per page, so both the content cards and the
tour film stand on real pixels of the real site. If a page changes, re-shoot and
rebuild rather than redrawing it. The captures are scratch, they are gitignored.

## 6. Asset pipelines

All exporters run in the browser against `tools/serve.py`, which writes POSTed
files to `tools/out/`.

| Asset | Page | Call |
|---|---|---|
| Logo, icons, og-image | `/brand/export-logo.html` | `LOGOS.all()` |
| Social pack | `/brand/export.html` | `EXPORT.all()` |
| Twitter set (10 explainers) | `/brand/export-twitter.html` | `TW.all()`, and `TW.collisions()` must say clean for all ten |
| Films → frames | `/brand/motion/0X-*.html?rec=1` | `RENDER.run({fps:30})`, then ffmpeg |

TICK is the exception and the direction of travel: he never touches a browser.

| Asset | Command |
|---|---|
| Site captures | `python tools/shots.py`, headless Chrome, tall PNGs into `tools/_shots/` |
| Content cards | `python tools/tick_content.py`, real captures + TICK, every card must report clean |
| Site tour film | `python tools/tick_tour.py`, `--preview` first |
| TICK poses | `python tools/tick_poses.py`, one image per pose plus cutouts |
| TICK cards | `python tools/tick_cards.py`, every card must report clean |
| TICK film (MP4) | `python tools/tick_film.py`, `--preview` for eight frames first |

Then `python tools/build_png.py` assembles `png/`. **No contact sheets.** The
operator asked for content as separate full images, not thumbnails tiled into
one picture, so every file in `png/` is one thing filling its own frame.
Compress big PNGs with Pillow `quantize(256)`; it cuts ~60% with no visible loss.

`build_png.py` distinguishes **derived** folders (01, 02, 05, 06;
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

No contracts, no chain integration, no custody, no wallet, no KYC or
jurisdiction gating, no decentralised oracle. Resolution is a human with
`POLYMARCT_ADMIN_TOKEN`. The public host is static, so the live site runs in
demo mode. `ARCHITECTURE.md` specifies the on chain work, `AUDIT.md` lists what
is open. Real money is blocked on legal clearance, not on code.

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
