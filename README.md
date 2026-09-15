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

## Code

- `assets/css/polymarct.css` — the whole design system
- `assets/js/data.js` — 50 markets across 7 categories, each with resolution criteria and a named source; Arc telemetry, protocols, traders, themes
- `assets/js/engine.js` — seeded history, live tick loop, momentum, EARLY, contrarian score, Future Index, theme aggregates, drivers
- `assets/js/ui.js` — header, footer, market card, sparkline, ticker, modals, toasts, terminal mode
- `assets/js/field.js` — the hero live market field canvas

## Design

Near black graphite, warm white, acidic electric green (`#CCFF00`), electric blue secondary. Hairlines, 2px radii, tabular numbers, huge tight tracked headlines, small uppercase mono metadata. No purple gradients, no glassmorphism, no rounded pill soup. Motion carries information only: probabilities tick, cards flash on the direction of the move, the chart breathes, the field drifts. `prefers-reduced-motion` stops the simulation loop and the field.

Terminal mode is a real mode, not a skin: header toggle, persisted in `localStorage`, denser grid, and it reveals market depth and trade history on the detail page.

## Status

Demonstration state. Every number is generated in the browser: no wallet, no orders, no settlement, no funds. See `ARCHITECTURE.md` for the contract, oracle, indexer and compliance layers that have to exist before a real money launch.
