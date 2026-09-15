/* POLYMARCT / market engine
   Deterministic history + a live simulation loop. In production this layer is
   replaced by the indexer websocket; the shape of the state stays identical. */

const PM = (() => {
  // ---- seeded rng so every reload draws the same history ----
  function rng(seed) {
    let s = 0;
    for (let i = 0; i < seed.length; i++) s = (s * 31 + seed.charCodeAt(i)) >>> 0;
    return () => {
      s ^= s << 13; s >>>= 0;
      s ^= s >> 17;
      s ^= s << 5; s >>>= 0;
      return s / 4294967296;
    };
  }

  // ---- formatting ----
  const fmt = {
    usd(n) {
      if (n >= 1e9) return "$" + (n / 1e9).toFixed(2) + "B";
      if (n >= 1e6) return "$" + (n / 1e6).toFixed(2) + "M";
      if (n >= 1e3) return "$" + (n / 1e3).toFixed(1) + "K";
      return "$" + n.toFixed(0);
    },
    usdExact(n) { return "$" + n.toLocaleString("en-US", { maximumFractionDigits: 0 }); },
    n(n) { return n.toLocaleString("en-US"); },
    pct(x, d = 1) { return (x * 100).toFixed(d) + "%"; },
    signed(x, d = 1) { return (x >= 0 ? "+" : "") + (x * 100).toFixed(d) + "%"; },
    cents(x) { return Math.round(x * 100) + "¢"; },
    left(iso) {
      const ms = new Date(iso) - Date.now();
      if (ms <= 0) return "CLOSED";
      const d = Math.floor(ms / 864e5), h = Math.floor(ms / 36e5) % 24, m = Math.floor(ms / 6e4) % 60;
      if (d > 0) return d + "D " + String(h).padStart(2, "0") + "H";
      return String(h).padStart(2, "0") + "H " + String(m).padStart(2, "0") + "M";
    },
    leftLong(iso) {
      const ms = new Date(iso) - Date.now();
      if (ms <= 0) return "CLOSED";
      const d = Math.floor(ms / 864e5), h = Math.floor(ms / 36e5) % 24, m = Math.floor(ms / 6e4) % 60;
      return d + "D " + String(h).padStart(2, "0") + "H " + String(m).padStart(2, "0") + "M";
    },
    date(iso) {
      return new Date(iso).toLocaleString("en-GB", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "UTC" }) + " UTC";
    },
    ago(ts) {
      const s = Math.floor((Date.now() - ts) / 1000);
      if (s < 60) return s + "s ago";
      if (s < 3600) return Math.floor(s / 60) + "m ago";
      return Math.floor(s / 3600) + "h ago";
    },
    clock(ts) {
      return new Date(ts).toLocaleTimeString("en-GB", { hour12: false });
    }
  };

  // ---- build state ----
  const state = { markets: [], events: [], index: [], subs: [] };

  MARKETS.forEach(m => {
    const r = rng(m.id);
    const hist = [];
    // 96 points of plausible drift landing exactly on the current probability
    let p = clamp(m.yes - m.d24 * 1.6 + (r() - 0.5) * 0.12);
    for (let i = 0; i < 96; i++) {
      p = clamp(p + (r() - 0.5) * 0.028 + (m.yes - p) * 0.035);
      hist.push(p);
    }
    hist[hist.length - 1] = m.yes;
    state.markets.push(Object.assign({}, m, {
      hist,
      open: m.yes - m.d24,
      vol24: m.vol * (0.08 + r() * 0.22),
      avgVol: m.vol * (0.09 + r() * 0.10),
      largest: Math.round(m.vol * (0.02 + r() * 0.05)),
      age: Math.floor(r() * 60) + 2,
      watchers: Math.round(m.traders * (0.4 + r() * 0.9)),
      lastMove: Date.now() - Math.floor(r() * 9e5),
      drivers: null
    }));
  });

  function clamp(x) { return Math.max(0.02, Math.min(0.98, x)); }
  function get(id) { return state.markets.find(m => m.id === id); }

  // ---- derived reads ----
  function momentum(m) {
    const a = Math.abs(m.d24), spread = Math.abs(m.yes - 0.5), volRatio = m.vol24 / m.avgVol;
    if (a >= 0.10 && volRatio > 1.6) return { label: "INFORMATION EVENT", rank: 10, tone: "acid" };
    if (a >= 0.08) return { label: "MOVING FAST", rank: 9, tone: "acid" };
    if (a >= 0.05 && Math.sign(m.d24) !== Math.sign(m.yes - 0.5)) return { label: "CONSENSUS SHIFTING", rank: 8, tone: "blue" };
    if (volRatio > 1.8) return { label: "HEATING UP", rank: 7, tone: "acid" };
    if (spread > 0.35) return { label: "EXTREME CONFIDENCE", rank: 4, tone: "" };
    if (spread < 0.03) return { label: "DEAD EVEN", rank: 6, tone: "blue" };
    if (a >= 0.03) return { label: "MARKET IN FLUX", rank: 5, tone: "" };
    if (Math.sign(m.d24) !== Math.sign(m.yes - 0.5) && a > 0.015) return { label: "CONTRARIAN", rank: 6, tone: "blue" };
    return { label: "STEADY", rank: 1, tone: "" };
  }

  // EARLY: thin volume, thickening activity, probability actually moving
  function isEarly(m) {
    return m.vol < 900000 && m.vol24 / m.avgVol > 1.25 && Math.abs(m.d24) > 0.015 && m.age < 40;
  }

  // AGAINST THE CROWD: lopsided book, money arriving on the unloved side
  function contrarianScore(m) {
    const conviction = Math.abs(m.yes - 0.5);
    const against = Math.sign(m.d24) !== Math.sign(m.yes - 0.5) ? Math.abs(m.d24) : 0;
    return conviction > 0.18 ? conviction * against * 100 : 0;
  }

  function sorted(key) {
    const c = state.markets.slice();
    if (key === "volume") return c.sort((a, b) => b.vol - a.vol);
    if (key === "moving") return c.sort((a, b) => Math.abs(b.d24) - Math.abs(a.d24));
    if (key === "new") return c.sort((a, b) => a.age - b.age);
    if (key === "closing") return c.sort((a, b) => new Date(a.ends) - new Date(b.ends));
    if (key === "early") return c.filter(isEarly).sort((a, b) => b.vol24 / b.avgVol - a.vol24 / a.avgVol);
    if (key === "contrarian") return c.filter(m => contrarianScore(m) > 0).sort((a, b) => contrarianScore(b) - contrarianScore(a));
    if (key === "signal") return c.sort((a, b) => momentum(b).rank - momentum(a).rank || Math.abs(b.d24) - Math.abs(a.d24));
    return c;
  }

  // THE FUTURE INDEX: aggregate confidence across a fixed basket
  function futureIndex() {
    const ms = FUTURE_INDEX_MEMBERS.map(get).filter(Boolean);
    const v = ms.reduce((s, m) => s + m.yes, 0) / ms.length * 100;
    const d = ms.reduce((s, m) => s + m.d24, 0) / ms.length * 100;
    return { value: v, delta: d, members: ms };
  }

  function themeReads() {
    return THEMES.map(t => {
      const ms = state.markets.filter(m => m.tags.some(x => t.tags.includes(x)));
      if (!ms.length) return null;
      const v = ms.reduce((s, m) => s + m.yes, 0) / ms.length;
      const d = ms.reduce((s, m) => s + m.d24, 0) / ms.length;
      const read = v > 0.62 ? "Bullish" : v < 0.42 ? "Bearish" : "Neutral";
      return { name: t.n, value: v, delta: d, read, n: ms.length };
    }).filter(Boolean);
  }

  // WHY IS IT MOVING: drivers, derived not invented
  function drivers(m) {
    const out = [];
    const ratio = m.vol24 / m.avgVol;
    out.push({ k: "24H VOLUME", v: fmt.usd(m.vol24), note: ratio.toFixed(1) + "x normal", weight: Math.min(1, ratio / 3) });
    out.push({ k: "LARGEST TRADE", v: fmt.usdExact(m.largest), note: "single fill", weight: Math.min(1, m.largest / (m.liq * 0.35)) });
    out.push({ k: "LIQUIDITY", v: fmt.usd(m.liq), note: (m.liq / m.vol > 0.3 ? "deepening" : "thin versus flow"), weight: Math.min(1, m.liq / m.vol) });
    out.push({ k: "TRADERS 24H", v: fmt.n(Math.round(m.traders * 0.08)), note: "unique addresses", weight: 0.4 });
    if (Math.abs(m.d24) > 0.06) out.push({ k: "INFORMATION EVENT", v: "DETECTED", note: "probability broke its 24h range", weight: 1 });
    return out.sort((a, b) => b.weight - a.weight);
  }

  // ---- live loop ----
  const EVENT_KINDS = [
    { k: "PROBABILITY", tone: "acid" },
    { k: "LARGE TRADE", tone: "" },
    { k: "VOLUME SPIKE", tone: "blue" },
    { k: "LIQUIDITY", tone: "" },
    { k: "CONSENSUS", tone: "blue" },
    { k: "MARKET MAKER", tone: "" }
  ];

  function seedEvents(n) {
    for (let i = 0; i < n; i++) pushEvent(true);
    state.events.sort((a, b) => b.ts - a.ts);
  }

  function pushEvent(seed) {
    const m = state.markets[Math.floor(Math.random() * state.markets.length)];
    const kind = EVENT_KINDS[Math.floor(Math.random() * EVENT_KINDS.length)];
    const ts = seed ? Date.now() - Math.floor(Math.random() * 36e5) : Date.now();
    let txt = "", val = "", tone = kind.tone;
    const side = Math.random() > 0.5 ? "YES" : "NO";
    const size = Math.round((2000 + Math.random() * 280000) / 100) * 100;

    switch (kind.k) {
      case "PROBABILITY": {
        const d = (Math.random() * 0.14 + 0.01) * (Math.random() > 0.45 ? 1 : -1);
        txt = m.q; val = fmt.signed(d); tone = d >= 0 ? "acid" : "no";
        break;
      }
      case "LARGE TRADE":
        txt = m.q; val = fmt.usdExact(size) + " " + side; tone = side === "YES" ? "acid" : "no";
        break;
      case "VOLUME SPIKE":
        txt = m.q; val = (1.8 + Math.random() * 4).toFixed(1) + "x avg"; tone = "blue";
        break;
      case "LIQUIDITY":
        txt = m.q; val = "+" + fmt.usd(20000 + Math.random() * 400000); tone = "";
        break;
      case "CONSENSUS":
        txt = m.q; val = Math.random() > 0.5 ? "YES → NO" : "NO → YES"; tone = "blue";
        break;
      case "MARKET MAKER":
        txt = m.q; val = "NEW MAKER"; tone = "";
        break;
    }
    state.events.unshift({ id: Math.random().toString(36).slice(2), kind: kind.k, tone, txt, val, ts, market: m.id });
    if (state.events.length > 160) state.events.pop();
  }

  function tick() {
    // move a handful of markets
    const n = 1 + Math.floor(Math.random() * 3);
    const touched = [];
    for (let i = 0; i < n; i++) {
      const m = state.markets[Math.floor(Math.random() * state.markets.length)];
      const step = (Math.random() - 0.5) * 0.024;
      const before = m.yes;
      m.yes = clamp(m.yes + step);
      m.d24 = m.yes - m.open;
      m.hist.push(m.yes);
      if (m.hist.length > 96) m.hist.shift();
      m.vol += Math.abs(step) * m.liq * 4;
      m.vol24 += Math.abs(step) * m.liq * 4;
      m.traders += Math.random() > 0.65 ? 1 : 0;
      m.lastMove = Date.now();
      touched.push({ m, dir: m.yes >= before ? 1 : -1 });
    }
    if (Math.random() > 0.45) pushEvent(false);
    state.subs.forEach(fn => { try { fn(touched); } catch (e) { console.error("[pm] subscriber failed", e); } });
  }

  function subscribe(fn) { state.subs.push(fn); return () => { state.subs = state.subs.filter(f => f !== fn); }; }

  let timer = null;
  function start() {
    if (timer) return;
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    timer = setInterval(tick, 1400);
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) { clearInterval(timer); timer = null; }
      else if (!timer) timer = setInterval(tick, 1400);
    });
  }

  seedEvents(40);

  return { state, get, fmt, rng, momentum, isEarly, contrarianScore, sorted, futureIndex, themeReads, drivers, subscribe, start, tick, clamp };
})();
