/* POLYMARCT / LIVE MARKET FIELD
   A financial star map. Thin lines, drifting probabilities, slow. */

(function () {
  const cv = document.getElementById("field");
  if (!cv) return;
  const ctx = cv.getContext("2d");
  const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  let W = 0, H = 0, dpr = 1, lines = [], labels = [], t = 0;

  const WORDS = ["BTC>125K", "ETH>5K", "ARC 1M TX", "FED CUT", "USDC 30%", "TVL 100M", "NVDA BEAT", "SOL/ETH", "ETF FLOW",
    "L2 ATH", "CPI", "RATES", "IPO", "AI CAPEX", "SUPPLY 300B", "PERPS LIVE", "STABLE 1B", "BRENT 90"];

  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = cv.clientWidth; H = cv.clientHeight;
    cv.width = W * dpr; cv.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    build();
  }

  function build() {
    lines = [];
    const n = Math.round(Math.min(260, Math.max(90, W / 6)));
    for (let i = 0; i < n; i++) {
      lines.push({
        x: Math.random() * W,
        y: Math.random() * H,
        len: 8 + Math.random() * 120,
        vx: (0.08 + Math.random() * 0.5) * (Math.random() > .5 ? 1 : -1),
        a: 0.04 + Math.random() * 0.16,
        hot: Math.random() > 0.94,
        tilt: (Math.random() - 0.5) * 0.16
      });
    }
    labels = [];
    const ln = Math.round(Math.min(44, Math.max(14, W / 42)));
    for (let i = 0; i < ln; i++) {
      labels.push({
        x: Math.random() * W,
        y: Math.random() * H,
        vx: (0.05 + Math.random() * 0.22) * (Math.random() > .5 ? 1 : -1),
        a: 0.10 + Math.random() * 0.26,
        txt: Math.random() > 0.55
          ? WORDS[(Math.random() * WORDS.length) | 0]
          : (Math.random() > 0.5
            ? (Math.random() * 100).toFixed(0) + "¢"
            : (Math.random() > 0.5 ? "+" : "-") + (Math.random() * 12).toFixed(1) + "%"),
        hot: Math.random() > 0.9,
        size: 9 + Math.random() * 3
      });
    }
  }

  function frame() {
    ctx.clearRect(0, 0, W, H);

    // faint structural grid
    ctx.strokeStyle = "rgba(242,239,233,.028)";
    ctx.lineWidth = 1;
    const gap = 96;
    ctx.beginPath();
    for (let x = (t * 0.06) % gap; x < W; x += gap) { ctx.moveTo(x, 0); ctx.lineTo(x, H); }
    for (let y = 0; y < H; y += gap) { ctx.moveTo(0, y); ctx.lineTo(W, y); }
    ctx.stroke();

    // probability lines
    lines.forEach(l => {
      l.x += l.vx * 0.42;
      if (l.x > W + l.len) l.x = -l.len;
      if (l.x < -l.len) l.x = W + l.len;
      ctx.beginPath();
      ctx.moveTo(l.x, l.y);
      ctx.lineTo(l.x + l.len, l.y + l.len * l.tilt);
      ctx.strokeStyle = l.hot ? `rgba(204,255,0,${l.a * 1.5})` : `rgba(242,239,233,${l.a})`;
      ctx.lineWidth = l.hot ? 1.1 : 0.7;
      ctx.stroke();
    });

    // drifting readouts
    ctx.font = "500 10px ui-monospace,SFMono-Regular,Menlo,monospace";
    labels.forEach(l => {
      l.x += l.vx * 0.3;
      if (l.x > W + 90) l.x = -90;
      if (l.x < -90) l.x = W + 90;
      ctx.font = `500 ${l.size.toFixed(1)}px ui-monospace,SFMono-Regular,Menlo,monospace`;
      ctx.fillStyle = l.hot ? `rgba(204,255,0,${l.a + .16})` : `rgba(242,239,233,${l.a})`;
      ctx.fillText(l.txt, l.x, l.y);
    });

    t++;
    if (!reduce) requestAnimationFrame(frame);
  }

  window.addEventListener("resize", resize, { passive: true });
  resize();
  frame();
})();
