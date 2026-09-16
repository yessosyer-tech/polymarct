# POLYMARCT // CONTENT PACK

38 images, rendered from live market state with the same code the product runs
on. Nothing here is an illustration of the product. It is the product.

Regenerate any time: `python tools/serve.py`, open `/brand/export.html`, run
`EXPORT.all()` in the console. Numbers refresh, layouts stay fixed.

---

## What is in the folder

| Set | Count | Size | What it is |
|---|---|---|---|
| `signal-*` | 8 | 1600×900 | A real market: question, probability, 24h change, sparkline, volume |
| `hook-*` | 10 | 1600×900 | One line of the brand argument, nothing else |
| `explainer-*` | 6 | 1600×900 | How a market works, the loop, the Verdict Engine, one asset one chain, the Conviction Index, why Arc |
| `stat-*` | 3 | 1600×900 | Future Index, What the World Thinks, the live board |
| `portrait-*` | 9 | 1080×1350 | Vertical cuts for feed footprint |
| `profile-header-1500x500` | 1 | 1500×500 | X header |
| `profile-avatar-400` | 1 | 400×400 | Profile picture |

16:9 fills the timeline without a crop. 4:5 takes roughly a third more vertical
space in the feed, which is why the portrait set exists.

---

## The rhythm that actually compounds

Growth here comes from being the account that already knows what moved, not
from posting more. Four slots a day, and two of them are reactions rather
than scheduled posts.

**Morning, one signal.** The market that moved most overnight. Post the
`signal-*` card and one line stating the move, not an opinion about it.

**Midday, one explainer or hook.** Alternate. New followers arrived overnight
and have no idea what this is; explainers convert them, hooks spread.

**When something breaks, one signal.** Not a take, a price. This is the slot
that earns follows, because you are the first account with a number instead of
an argument.

**Weekly, one stat card.** The Future Index or What the World Thinks, as a
recap of what the week priced in. This is the one that gets quoted.

Never post two hooks in a row. A hook without a number behind it is a poster,
and posters do not build a market.

---

## Copy that goes with each set

Short, flat, no exclamation marks. The number carries the post.

### Signal cards

> Spot BTC ETFs, $2B inflow week before December.
> The market has it at 58 cents. It was 46 on Tuesday.

> The Fed cuts at the next meeting: 71%.
> That is up 11 points in a week. Nobody changed their mind about the economy, they changed their mind about the Fed.

> Arc past 1M daily transactions before November: 42%.
> Priced by people who have to be right, not people who have to be loud.

Formula that works: **what the question is**, then **what the price is**, then
**what changed**. Stop there. Do not tell people what to think about it.

### Hook cards

Post the image with no caption, or with the same line repeated. These are for
reach, not conversion. They work as quote tweets on other people's arguments:
someone posts a confident take, you reply with "Everyone has an opinion. Only
the market has a price." and the relevant signal card.

### Explainer cards

> A market only works if the verdict cannot be argued with. Source named before
> trading opens, evidence published with the result, 24 hours to dispute it.

> One asset, one chain. USDC on Arc for collateral, fees and payouts. No
> bridges, no swaps, no second token, and you never need to hold $PMARC to trade.

> Size is not skill. The leaderboard ranks risk adjusted return on resolved
> positions, because ranking by volume just pays wash traders.

### Stat cards

> The Future Index, this week: 72.4, up 4.7.
> Ten markets, equally weighted. Confidence rising across crypto, technology and macro.

---

## Three threads worth writing once and pinning

**1. "What a prediction market actually is"** — explainer 01, then 03, then 04.
Four posts. This is the pinned thread. Every new follower reads it.

**2. "The week the market changed its mind"** — three signal cards from the
same week where the probability moved hard, in order, with the dates. Ends on
the stat card. This is the thread that gets shared by people who are not in
crypto, because it reads as journalism.

**3. "Why Arc"** — explainer 06 plus explainer 04. Two posts. Aimed at the Arc
ecosystem accounts, who will amplify it because it is about their chain.

---

## Rules that are not negotiable

- No price predictions of your own. You run the market, you do not have a take.
- No promised returns, no "guaranteed", no "risk free", no APY. Not in an image,
  not in a caption, not in a reply.
- $PMARC is never the hook. The product is the hook. If the token leads, the
  account reads as a token account and the people worth having leave.
- Never post a number you cannot point at. Every figure in these images comes
  from the market state; keep it that way when you write captions.
- The domain stays off every asset until the real one is live. One constant in
  `brand/brand-render.js` switches it on everywhere.

---

## Making more

Add a hook to the `HOOKS` array or a row set to `EXPLAINERS` in
`brand/export.html` and re-run the export. New markets appear in the signal set
automatically, since the manifest pulls the current top movers.
