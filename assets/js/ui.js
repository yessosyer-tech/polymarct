/* POLYMARCT / shared interface layer
   Header, footer, cards, sparklines, ticker, modals, terminal mode. */

const UI = (() => {
  const NAV = [
    ["MARKETS", "markets.html"],
    ["DISCOVER", "discover.html"],
    ["SIGNALS", "signals.html"],
    ["MAP", "map.html"],
    ["ARC", "arc.html"],
    ["LEADERBOARD", "leaderboard.html"],
    ["$PMARC", "token.html"]
  ];

  /* THE SPLIT UNIT: one square is one unit of probability, and the boundary
     between the YES mass and the NO void is the price path itself. */
  const GLYPH = `<svg class="glyph" viewBox="0 0 64 64" aria-hidden="true" style="width:19px;height:19px;flex:none">
    <g fill="currentColor">
    <rect x="8" y="7" width="9" height="50" fill="currentColor"/>
    <rect x="8" y="7" width="20" height="8" fill="currentColor"/>
    <rect x="8" y="49" width="20" height="8" fill="currentColor"/>
    <rect x="47" y="19" width="9" height="26" fill="currentColor"/>
    <rect x="36" y="19" width="20" height="8" fill="currentColor"/>
    <rect x="36" y="37" width="20" height="8" fill="currentColor"/>
    </g>
    <rect x="29" y="26" width="6" height="12" fill="var(--acid)"/>
  </svg>`;

  function header(active) {
    const links = NAV.map(([n, h]) => `<a href="${h}" class="${h === active ? "on" : ""}">${n}</a>`).join("");
    return `<header class="hdr"><div class="wrap">
      <a class="logo" href="index.html">${GLYPH}POLYMARCT</a>
      <nav class="nav" id="nav">${links}</nav>
      <div class="hdr-right">
        <div class="modeswitch" id="modeswitch">
          <button data-mode="simple">SIMPLE</button><button data-mode="terminal">TERMINAL</button>
        </div>
        <button class="btn btn--sm" id="connect">CONNECT WALLET</button>
        <button class="burger" id="burger" aria-label="Menu"><span></span></button>
      </div>
    </div></header>`;
  }

  function footer() {
    return `<footer class="ftr"><div class="wrap">
      <div class="ftr-grid">
        <div>
          <div class="logo" style="margin-bottom:12px">${GLYPH}POLYMARCT</div>
          <p class="lede" style="font-size:14px;max-width:34ch">The leading prediction market on Arc. Price the future, follow the signal, let the market decide.</p>
        </div>
        <div><h4>MARKET</h4>
          <a href="markets.html">All markets</a><a href="discover.html">Discover</a><a href="signals.html">The Signal</a><a href="map.html">Market Map</a><a href="create.html">Create a market</a></div>
        <div><h4>ECOSYSTEM</h4>
          <a href="arc.html">Arc // Live</a><a href="leaderboard.html">Conviction Index</a><a href="token.html">$PMARC</a><a href="verdict.html">The Verdict Engine</a></div>
        <div><h4>INFORMATION</h4>
          <a href="verdict.html#rules">Resolution rules</a><a href="verdict.html#dispute">Dispute window</a><a href="verdict.html#risk">Risk disclosure</a><a href="404.html">Status</a></div>
      </div>
      <p class="legal">
        Polymarct is an information market. Positions are collateralised and settled exclusively in USDC on Arc; no other asset, token or chain is accepted. Trading outcome positions carries risk, including total loss of the amount committed to a position. Nothing on this site is investment advice, and no return is promised, implied or guaranteed. $PMARC is an ecosystem asset, not an investment product or a claim on revenue. Access is subject to jurisdiction gating, eligibility checks and age restrictions where required by law. Market data shown in this build is demonstration data.
      </p>
      <p class="legal" style="border:0;margin-top:10px;padding-top:0">POLYMARCT // BUILT FOR ARC. BUILT FOR MARKETS.</p>
    </div></footer>`;
  }

  function mount(active) {
    document.body.insertAdjacentHTML("afterbegin", header(active));
    document.body.insertAdjacentHTML("beforeend", footer());
    document.body.insertAdjacentHTML("beforeend", `<div class="toasts" id="toasts"></div>
      <div class="modal" id="modal"><div class="modal-box" id="modal-box"></div></div>`);

    document.getElementById("burger").onclick = () => document.getElementById("nav").classList.toggle("open");
    document.getElementById("modal").onclick = e => { if (e.target.id === "modal") closeModal(); };
    document.addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });

    const mode = localStorage.getItem("pm.mode") || "simple";
    setMode(mode);
    document.querySelectorAll("#modeswitch button").forEach(b => b.onclick = () => setMode(b.dataset.mode));

    document.getElementById("connect").onclick = () => {
      openModal(`<div class="panel-h">WALLET</div>
        <h3 class="h3" style="margin-bottom:12px">CONNECT TO ARC</h3>
        <p class="muted" style="font-size:14px;margin-top:0">Polymarct takes one asset on one chain: USDC on Arc. No ETH, no other token, no bridging in from somewhere else, no card. A wallet holding anything else has nothing to trade with here. This build runs on demonstration state, so nothing touches funds.</p>
        <div class="kv"><span class="k">NETWORK</span><span>ARC MAINNET</span></div>
        <div class="kv"><span class="k">ACCEPTED ASSET</span><span class="acid">USDC ONLY</span></div>
        <div class="kv"><span class="k">SETTLEMENT</span><span>USDC ON ARC</span></div>
        <div class="kv"><span class="k">STATUS</span><span class="acid">DEMO STATE</span></div>
        <button class="btn btn--block" style="margin-top:18px" onclick="UI.closeModal()">CLOSE</button>`);
    };
  }

  function setMode(m) {
    document.body.dataset.mode = m;
    localStorage.setItem("pm.mode", m);
    document.querySelectorAll("#modeswitch button").forEach(b => b.classList.toggle("on", b.dataset.mode === m));
  }

  function openModal(html) {
    document.getElementById("modal-box").innerHTML = html;
    document.getElementById("modal").classList.add("open");
  }
  function closeModal() { document.getElementById("modal").classList.remove("open"); }

  function toast(msg) {
    const t = document.createElement("div");
    t.className = "toast";
    t.textContent = msg;
    document.getElementById("toasts").appendChild(t);
    setTimeout(() => t.remove(), 4200);
  }

  /* ---------- sparkline ---------- */
  function spark(hist, w, h, color) {
    const pts = hist.slice(-48);
    const min = Math.min(...pts), max = Math.max(...pts), range = (max - min) || 0.01;
    const d = pts.map((p, i) => {
      const x = (i / (pts.length - 1)) * w;
      const y = h - ((p - min) / range) * (h - 3) - 1.5;
      return (i ? "L" : "M") + x.toFixed(1) + " " + y.toFixed(1);
    }).join(" ");
    const last = pts[pts.length - 1], lx = w, ly = h - ((last - min) / range) * (h - 3) - 1.5;
    return `<svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true">
      <path d="${d}" fill="none" stroke="${color}" stroke-width="1.25" vector-effect="non-scaling-stroke"/>
      <circle cx="${lx - 1}" cy="${ly.toFixed(1)}" r="1.6" fill="${color}"/>
    </svg>`;
  }

  function meter(rank) {
    let s = "";
    for (let i = 0; i < 10; i++) s += `<i class="${i < rank ? "on" : ""}"></i>`;
    return `<span class="meter">${s}</span>`;
  }

  /* ---------- market card ---------- */
  function card(m) {
    const mo = PM.momentum(m);
    const early = PM.isEarly(m);
    const up = m.d24 >= 0;
    return `<a class="card" data-id="${m.id}" href="market.html?m=${m.id}">
      <div class="card-top">
        <span class="cat">${m.cat}</span>
        <span class="row" style="gap:6px">
          ${early ? `<span class="chip chip--solid">EARLY</span>` : ""}
          <span class="chip ${mo.tone === "acid" ? "chip--acid" : mo.tone === "blue" ? "chip--blue" : ""}">${mo.label}</span>
        </span>
      </div>
      <div class="q">${m.q}</div>
      <div class="prob">
        <span class="p" data-f="p">${Math.round(m.yes * 100)}<span style="font-size:.42em;letter-spacing:.02em">%</span></span>
        <span class="chg ${up ? "up" : "down"}" data-f="d">${PM.fmt.signed(m.d24)}</span>
      </div>
      <div data-f="spark">${spark(m.hist, 300, 34, "var(--acid)")}</div>
      <div class="legs">
        <span class="leg leg--yes"><span class="lbl">TAKE YES</span><span class="val" data-f="y">${PM.fmt.cents(m.yes)}</span></span>
        <span class="leg leg--no"><span class="lbl">TAKE NO</span><span class="val" data-f="n">${PM.fmt.cents(1 - m.yes)}</span></span>
      </div>
      <div class="cardmeta">
        <span data-f="v">${PM.fmt.usd(m.vol)} VOL</span>
        <span>${PM.fmt.n(m.traders)} TRADERS</span>
        <span>${PM.fmt.left(m.ends)} LEFT</span>
      </div>
    </a>`;
  }

  function cards(list, el) {
    if (!list.length) { el.outerHTML = empty(); return; }
    el.innerHTML = list.map(card).join("");
  }

  function empty(kind) {
    if (kind === "quiet") return `<div class="empty"><h3>QUIET.</h3><p>That's unusual.</p></div>`;
    return `<div class="empty"><h3>NOTHING HERE YET.</h3><p>The future hasn't given us enough to trade on.</p></div>`;
  }

  /* live-patch the cards already on screen */
  function bindLive(root) {
    PM.subscribe(touched => {
      touched.forEach(({ m, dir }) => {
        (root || document).querySelectorAll(`.card[data-id="${m.id}"]`).forEach(el => {
          const q = s => el.querySelector(`[data-f="${s}"]`);
          if (q("p")) q("p").innerHTML = Math.round(m.yes * 100) + `<span style="font-size:.42em;letter-spacing:.02em">%</span>`;
          if (q("d")) { q("d").textContent = PM.fmt.signed(m.d24); q("d").className = "chg " + (m.d24 >= 0 ? "up" : "down"); }
          if (q("y")) q("y").textContent = PM.fmt.cents(m.yes);
          if (q("n")) q("n").textContent = PM.fmt.cents(1 - m.yes);
          if (q("v")) q("v").textContent = PM.fmt.usd(m.vol) + " VOL";
          if (q("spark")) q("spark").innerHTML = spark(m.hist, 300, 34, "var(--acid)");
          el.classList.remove("flash", "flash-dn");
          void el.offsetWidth;
          el.classList.add(dir > 0 ? "flash" : "flash-dn");
        });
      });
    });
  }

  /* ---------- ticker ---------- */
  function ticker(el) {
    const render = () => {
      const items = PM.sorted("moving").slice(0, 16).map(m => {
        const up = m.d24 >= 0;
        const label = m.q.length > 52 ? m.q.slice(0, 50).trimEnd() + "…" : m.q;
        return `<span class="tick"><b>${label}</b>
          <span>${Math.round(m.yes * 100)}%</span>
          <span class="${up ? "up" : "down"}">${PM.fmt.signed(m.d24)}</span></span>`;
      }).join("");
      el.innerHTML = `<div class="ticker-track">${items}${items}</div>`;
    };
    render();
    setInterval(render, 30000);
  }

  /* ---------- why is it moving ---------- */
  function whyModal(id) {
    const m = PM.get(id);
    const ds = PM.drivers(m);
    openModal(`<div class="panel-h"><span>WHY IS IT MOVING</span><span class="mono">${m.cat}</span></div>
      <h3 class="h3" style="margin-bottom:16px">${m.q}</h3>
      <div class="prob" style="margin-bottom:18px">
        <span class="p" style="font-size:52px">${Math.round(m.yes * 100)}%</span>
        <span class="chg ${m.d24 >= 0 ? "up" : "down"}" style="font-size:14px">${PM.fmt.signed(m.d24)} / 24H</span>
      </div>
      ${ds.map(d => `<div class="kv"><span class="k">${d.k}</span><span>${d.v} <span class="muted">// ${d.note}</span></span></div>`).join("")}
      <p class="muted" style="font-size:12.5px;line-height:1.6;margin-top:16px">Drivers are derived from order flow and liquidity on this market. Polymarct does not tell you what to think about them.</p>
      <button class="btn btn--block" style="margin-top:14px" onclick="UI.closeModal()">CLOSE</button>`);
  }

  return { mount, card, cards, cards, spark, meter, empty, bindLive, ticker, toast, openModal, closeModal, whyModal, GLYPH, setMode };
})();
