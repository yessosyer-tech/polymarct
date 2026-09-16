/* POLYMARCT / brand renderer
   Every social artifact is drawn at export resolution on canvas, from the same
   primitives the site uses: hairline grid, market field, tabular numbers,
   one acid accent. No stock, no filters, no generated imagery. */

const BRAND = (() => {

  const FORMATS = [
    { id:"og",     label:"OG / LINK PREVIEW", w:1200, h:630  },
    { id:"x",      label:"X HEADER",          w:1500, h:500  },
    { id:"square", label:"SIGNAL CARD",       w:1080, h:1080 },
    { id:"story",  label:"STORY / VERTICAL",  w:1080, h:1920 },
    { id:"quote",  label:"HOOK CARD",         w:1080, h:1350 },
    { id:"banner", label:"WIDE BANNER",       w:2560, h:640  }
  ];

  const THEMES = {
    black: { bg:"#08090A", fg:"#F2EFE9", dim:"#8A8F94", line:"rgba(242,239,233,.10)", acc:"#CCFF00", neg:"#FF4D2E", panel:"#0D0F11" },
    acid:  { bg:"#CCFF00", fg:"#08090A", dim:"rgba(8,9,10,.62)", line:"rgba(8,9,10,.16)", acc:"#08090A", neg:"#8A1600", panel:"rgba(8,9,10,.06)" },
    warm:  { bg:"#F2EFE9", fg:"#08090A", dim:"#5C6166", line:"rgba(8,9,10,.12)", acc:"#6F8F00", neg:"#C0341B", panel:"rgba(8,9,10,.04)" }
  };

  const SANS = "'Inter Tight','Inter',Helvetica,Arial,sans-serif";
  const MONO = "'JetBrains Mono',ui-monospace,Menlo,monospace";
  /* Domain is deliberately not shown on any asset yet. When the real domain
     lands, set SIG to it here and every format picks it up. */
  const SIG  = "$PMARC // ON ARC";

  function rng(seed){
    let s = 0; for (let i=0;i<seed.length;i++) s = (s*31 + seed.charCodeAt(i))>>>0;
    return () => { s^=s<<13; s>>>=0; s^=s>>17; s^=s<<5; s>>>=0; return s/4294967296; };
  }

  /* ---------- type ---------- */
  function setFont(ctx, { size, weight=500, mono=false, track=0 }){
    ctx.font = `${weight} ${size}px ${mono?MONO:SANS}`;
    if ("letterSpacing" in ctx) ctx.letterSpacing = track + "px";
    return "letterSpacing" in ctx;
  }

  function text(ctx, str, x, y, o={}){
    const native = setFont(ctx, o);
    ctx.fillStyle = o.color || "#fff";
    ctx.textBaseline = o.baseline || "alphabetic";
    if (native || !o.track){ ctx.fillText(str, x, y); return ctx.measureText(str).width; }
    let cx = x;                                   // manual tracking fallback
    for (const ch of str){ ctx.fillText(ch, cx, y); cx += ctx.measureText(ch).width + o.track; }
    return cx - x;
  }

  function measure(ctx, str, o={}){ setFont(ctx, o); return ctx.measureText(str).width; }

  function wrap(ctx, str, maxw, o={}){
    setFont(ctx, o);
    const words = str.split(/\s+/), lines = [];
    let line = "";
    for (const w of words){
      const t = line ? line + " " + w : w;
      if (ctx.measureText(t).width > maxw && line){ lines.push(line); line = w; }
      else line = t;
    }
    if (line) lines.push(line);
    return lines;
  }

  function block(ctx, str, x, y, maxw, o={}){
    const lines = wrap(ctx, str, maxw, o);
    const lh = o.lh || o.size * 1.06;
    lines.forEach((l,i)=> text(ctx, l, x, y + i*lh, o));
    return y + (lines.length-1)*lh;
  }

  /* ---------- ground ---------- */
  function grid(ctx, w, h, gap, color){
    ctx.strokeStyle = color; ctx.lineWidth = 1;
    ctx.beginPath();
    for (let x=gap; x<w; x+=gap){ ctx.moveTo(x+.5,0); ctx.lineTo(x+.5,h); }
    for (let y=gap; y<h; y+=gap){ ctx.moveTo(0,y+.5); ctx.lineTo(w,y+.5); }
    ctx.stroke();
  }

  /* the live market field, frozen into a still */
  function field(ctx, w, h, seed, t, density=1){
    const r = rng(seed);
    const n = Math.round((w*h)/5200 * density);
    for (let i=0;i<n;i++){
      const x = r()*w, y = r()*h, len = 10 + r()*(w*0.13), tilt = (r()-.5)*0.18;
      const hot = r() > 0.94;
      ctx.beginPath(); ctx.moveTo(x,y); ctx.lineTo(x+len, y+len*tilt);
      ctx.strokeStyle = hot ? hexa(t.acc, .34) : hexa(t.fg, .05 + r()*0.10);
      ctx.lineWidth = hot ? 2 : 1.2;
      ctx.stroke();
    }
    const words = ["BTC>125K","ETH>5K","ARC 1M TX","FED CUT","USDC 30%","TVL 100M","+8.4%","-3.1%","67¢","41¢","VOL 4.8M","EARLY","LIVE"];
    const ln = Math.round(n/9);
    for (let i=0;i<ln;i++){
      const x = r()*w, y = r()*h, hot = r()>0.88;
      text(ctx, words[(r()*words.length)|0], x, y, {
        size: 12 + r()*8, mono:true, weight:500, track:1.2,
        color: hot ? hexa(t.acc,.42) : hexa(t.fg, .09 + r()*0.13)
      });
    }
  }

  function grain(ctx, w, h, amt){
    const img = ctx.getImageData(0,0,w,h), d = img.data;
    for (let i=0;i<d.length;i+=4){
      const v = (Math.random()-0.5) * amt;
      d[i]+=v; d[i+1]+=v; d[i+2]+=v;
    }
    ctx.putImageData(img,0,0);
  }

  function vignette(ctx, w, h, t){
    const g = ctx.createRadialGradient(w/2,h/2,Math.min(w,h)*0.25, w/2,h/2, Math.max(w,h)*0.78);
    g.addColorStop(0,"rgba(0,0,0,0)");
    g.addColorStop(1, t.bg === "#08090A" ? "rgba(0,0,0,.55)" : "rgba(0,0,0,.10)");
    ctx.fillStyle = g; ctx.fillRect(0,0,w,h);
  }

  function hexa(hex, a){
    if (hex.startsWith("rgba")) return hex;
    const n = parseInt(hex.slice(1),16);
    return `rgba(${(n>>16)&255},${(n>>8)&255},${n&255},${a})`;
  }

  /* ---------- components ---------- */
  /* THE BOOK. Two sides of the order book facing each other; the acid bar
     standing in the gap between them is the last price. */
  const EDGE = [[30,6],[30,20],[44,20],[44,32],[22,32],[22,44],[38,44],[38,58]];

  function mark(ctx, x, y, s, t){
    const u = s/64;
    ctx.save(); ctx.translate(x,y); ctx.scale(u,u);
    ctx.fillStyle = t.fg;
    [[8,7,9,50],[8,7,20,8],[8,49,20,8],[47,19,9,26],[36,19,20,8],[36,37,20,8]]
      .forEach(([rx,ry,rw,rh]) => ctx.fillRect(rx,ry,rw,rh));
    ctx.fillStyle = t.acc; ctx.fillRect(29,26,6,12);   // the last price, in the spread
    ctx.restore();
  }

  function lockup(ctx, x, y, s, t, withTag){
    mark(ctx, x, y, s, t);
    text(ctx, "POLYMARCT", x + s*1.34, y + s*0.86, {
      size: s*0.72, weight:600, track: -s*0.035, color: t.fg });
    if (withTag) text(ctx, "THE LEADING PREDICTION MARKET ON ARC", x + s*1.36, y + s*1.24, {
      size: s*0.19, mono:true, track: s*0.055, color: t.dim });
  }

  function probBar(ctx, x, y, w, h, p, t){
    ctx.fillStyle = hexa(t.fg,.12); ctx.fillRect(x,y,w,h);
    ctx.fillStyle = t.acc; ctx.fillRect(x,y,w*p,h);
    ctx.fillStyle = t.bg; ctx.fillRect(x + w*p - 1, y - h*0.9, 2, h*2.8);
  }

  function rule(ctx, x, y, w, t, a){ ctx.fillStyle = hexa(t.fg, a||.16); ctx.fillRect(x,y,w,1); }

  function metaRow(ctx, x, y, gap, items, t, size){
    let cx = x;
    items.forEach((s,i)=>{
      if (i){ ctx.fillStyle = hexa(t.fg,.26); text(ctx,"//",cx,y,{size,mono:true,track:size*.12,color:hexa(t.fg,.26)}); cx += measure(ctx,"//",{size,mono:true}) + gap; }
      const wd = text(ctx, s, cx, y, { size, mono:true, track:size*.12, color:t.dim });
      cx += wd + gap;
    });
  }

  function eyebrow(ctx, x, y, label, t, size){
    ctx.beginPath(); ctx.arc(x+size*.3, y - size*.32, size*.3, 0, 7);
    ctx.fillStyle = t.acc; ctx.fill();
    text(ctx, label, x + size*1.1, y, { size, mono:true, track:size*.22, color:t.dim });
  }

  /* ---------- formats ---------- */
  const R = {};

  R.og = (ctx, w, h, t, o) => {
    const m = o.market;
    field(ctx, w, h, m.id+"og", t, 1.1);
    vignette(ctx, w, h, t);
    ctx.fillStyle = hexa(t.bg,.62); ctx.fillRect(0,0,w*0.60,h);
    const P = 72;
    lockup(ctx, P, 62, 46, t, false);
    text(ctx, "THE FUTURE", P, 300, { size:118, weight:600, track:-6, color:t.fg });
    text(ctx, "HAS A PRICE.", P, 404, { size:118, weight:600, track:-6, color:t.fg });
    rule(ctx, P, 448, 420, t, .24);
    text(ctx, "THE LEADING PREDICTION MARKET ON ARC", P, 492, { size:19, mono:true, track:4.6, color:t.dim });
    text(ctx, SIG, P, 556, { size:19, mono:true, track:4.6, color:t.acc });

    // live readout on the right
    const bx = w - 430;
    ctx.fillStyle = hexa(t.fg,.05); ctx.fillRect(bx-32, 150, 392, 330);
    ctx.strokeStyle = hexa(t.fg,.18); ctx.lineWidth = 1; ctx.strokeRect(bx-32.5, 149.5, 392, 330);
    const lines = wrap(ctx, m.q.toUpperCase(), 328, { size:17, mono:true, track:2.2 });
    lines.slice(0,3).forEach((l,i)=> text(ctx, l, bx, 196 + i*26, { size:17, mono:true, track:2.2, color:t.dim }));
    text(ctx, Math.round(m.yes*100) + "%", bx, 356, { size:116, weight:600, track:-5, color:t.fg });
    text(ctx, "YES", bx + measure(ctx, Math.round(m.yes*100)+"%", {size:116,weight:600}) + 18, 356, { size:24, mono:true, track:5, color:t.dim });
    probBar(ctx, bx, 386, 328, 6, m.yes, t);
    metaRow(ctx, bx, 432, 14, [PM.fmt.usd(m.vol)+" VOL", PM.fmt.n(m.traders)+" TRADERS"], t, 15);
  };

  R.x = (ctx, w, h, t, o) => {
    field(ctx, w, h, "xheader", t, 0.9);
    vignette(ctx, w, h, t);
    grid(ctx, w, h, 100, t.line);
    // keep the lower left clear, the avatar sits there
    lockup(ctx, 300, 128, 64, t, false);
    text(ctx, "THE FUTURE HAS A PRICE.", 300, 300, { size:74, weight:600, track:-3.4, color:t.fg });
    text(ctx, "TRADE ON WHAT HAPPENS NEXT // " + SIG, 300, 352, { size:18, mono:true, track:4.4, color:t.acc });
    // ticker strip
    rule(ctx, 0, h-64, w, t, .16);
    const ms = PM.sorted("moving").slice(0,5);
    let cx = 300;
    ms.forEach(m=>{
      const lab = m.q.replace(/^Will\s+/,"").slice(0,26).toUpperCase();
      cx += text(ctx, lab, cx, h-30, { size:15, mono:true, track:2.4, color:t.dim }) + 14;
      cx += text(ctx, Math.round(m.yes*100)+"%", cx, h-30, { size:15, mono:true, track:2.4, color:t.fg }) + 10;
      cx += text(ctx, PM.fmt.signed(m.d24), cx, h-30, { size:15, mono:true, track:2.4, color: m.d24>=0?t.acc:t.neg }) + 34;
    });
  };

  R.banner = (ctx, w, h, t, o) => {
    field(ctx, w, h, "banner", t, 0.8);
    vignette(ctx, w, h, t);
    lockup(ctx, 140, 180, 88, t, true);
    text(ctx, "THE #1 MARKET FOR WHAT HAPPENS NEXT.", 140, 470, { size:44, weight:600, track:-1.8, color:t.fg });
    text(ctx, SIG, w-140-measure(ctx,SIG,{size:22,mono:true,track:5}), 470, { size:22, mono:true, track:5, color:t.acc });
    rule(ctx, 140, 510, w-280, t, .2);
  };

  R.square = (ctx, w, h, t, o) => {
    const m = o.market, P = 84;
    field(ctx, w, h, m.id+"sq", t, 0.9);
    vignette(ctx, w, h, t);
    eyebrow(ctx, P, 106, "POLYMARCT SIGNAL", t, 20);
    text(ctx, m.cat, w-P-measure(ctx,m.cat,{size:20,mono:true,track:4.4}), 106, { size:20, mono:true, track:4.4, color:t.dim });
    rule(ctx, P, 136, w-P*2, t, .18);

    const q = o.headline || m.q;
    const end = block(ctx, q, P, 262, w-P*2, { size:60, weight:500, track:-2.2, color:t.fg, lh:66 });

    const pct = Math.round(m.yes*100) + "%";
    text(ctx, pct, P, 726, { size:260, weight:600, track:-14, color:t.fg });
    const pw = measure(ctx, pct, { size:260, weight:600, track:-14 });
    text(ctx, "YES", P + pw + 28, 726, { size:38, mono:true, track:7, color:t.dim });
    text(ctx, PM.fmt.signed(m.d24), P + pw + 28, 664, { size:40, weight:600, track:-1, color: m.d24>=0?t.acc:t.neg });

    probBar(ctx, P, 772, w-P*2, 10, m.yes, t);
    text(ctx, "YES " + PM.fmt.cents(m.yes), P, 820, { size:22, mono:true, track:4, color:t.acc });
    const no = "NO " + PM.fmt.cents(1-m.yes);
    text(ctx, no, w-P-measure(ctx,no,{size:22,mono:true,track:4}), 820, { size:22, mono:true, track:4, color:t.dim });

    rule(ctx, P, 892, w-P*2, t, .18);
    metaRow(ctx, P, 934, 16, [PM.fmt.usd(m.vol)+" VOLUME", PM.fmt.n(m.traders)+" TRADERS", PM.fmt.left(m.ends)+" LEFT"], t, 20);
    mark(ctx, P, 976, 44, t);
    text(ctx, SIG, w-P-measure(ctx,SIG,{size:20,mono:true,track:4}), 1010, { size:20, mono:true, track:4, color:t.dim });
  };

  R.story = (ctx, w, h, t, o) => {
    const m = o.market, P = 84;
    field(ctx, w, h, m.id+"st", t, 0.75);
    vignette(ctx, w, h, t);
    lockup(ctx, P, 150, 52, t, false);
    eyebrow(ctx, P, 360, "LIVE ON ARC", t, 22);
    rule(ctx, P, 392, w-P*2, t, .18);

    block(ctx, o.headline || m.q, P, 530, w-P*2, { size:66, weight:500, track:-2.4, color:t.fg, lh:74 });

    const pct = Math.round(m.yes*100) + "%";
    text(ctx, pct, P, 1120, { size:280, weight:600, track:-16, color:t.fg });
    text(ctx, "YES", P, 1188, { size:40, mono:true, track:8, color:t.dim });
    text(ctx, PM.fmt.signed(m.d24) + " / 24H", P + 180, 1188, { size:40, mono:true, track:4, color: m.d24>=0?t.acc:t.neg });

    probBar(ctx, P, 1250, w-P*2, 12, m.yes, t);
    metaRow(ctx, P, 1320, 18, [PM.fmt.usd(m.vol)+" VOL", PM.fmt.n(m.traders)+" TRADERS"], t, 22);

    // the loop, drawn as a ladder
    const steps = ["DISCOVER","TRADE","FOLLOW","RESOLVE","SETTLE"];
    let y = 1470;
    steps.forEach((s,i)=>{
      const on = i < 3;
      text(ctx, String(i+1).padStart(2,"0"), P, y, { size:22, mono:true, track:3, color: hexa(t.fg,.34) });
      text(ctx, s, P+70, y, { size:34, weight:600, track:-.6, color: on ? t.fg : hexa(t.fg,.34) });
      if (on){ ctx.fillStyle = t.acc; ctx.fillRect(w-P-14, y-22, 14, 14); }
      y += 62;
    });

    text(ctx, SIG, P, h-110, { size:24, mono:true, track:5, color:t.acc });
  };

  R.quote = (ctx, w, h, t, o) => {
    const P = 84;
    field(ctx, w, h, (o.hook||"hook").slice(0,12), t, 0.7);
    vignette(ctx, w, h, t);
    lockup(ctx, P, 140, 48, t, false);
    rule(ctx, P, 300, w-P*2, t, .18);
    block(ctx, o.hook || "THE FUTURE DOESN'T ANNOUNCE ITSELF. IT MOVES.", P, 500, w-P*2,
      { size:96, weight:600, track:-4.4, color:t.fg, lh:98 });
    rule(ctx, P, h-260, w-P*2, t, .18);
    text(ctx, "POLYMARCT", P, h-190, { size:30, weight:600, track:-1, color:t.fg });
    text(ctx, SIG, P, h-140, { size:22, mono:true, track:5, color:t.acc });
    // probability signature: a small sparkline of a real market
    const m = o.market, pts = m.hist.slice(-40), bw = 320, bh = 90, bx = w-P-bw, by = h-250;
    const mn = Math.min(...pts), mx = Math.max(...pts), rg = (mx-mn)||.01;
    ctx.beginPath();
    pts.forEach((p,i)=>{ const x = bx + (i/(pts.length-1))*bw, y = by + bh - ((p-mn)/rg)*bh;
      i ? ctx.lineTo(x,y) : ctx.moveTo(x,y); });
    ctx.strokeStyle = t.acc; ctx.lineWidth = 2.4; ctx.stroke();
  };

  /* ---------- api ---------- */
  async function draw(canvas, id, o){
    const f = FORMATS.find(x=>x.id===id);
    const t = THEMES[o.theme] || THEMES.black;
    canvas.width = f.w; canvas.height = f.h;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = t.bg; ctx.fillRect(0,0,f.w,f.h);
    if (document.fonts && document.fonts.ready) await document.fonts.ready;
    R[id](ctx, f.w, f.h, t, o);
    grain(ctx, f.w, f.h, t.bg === "#08090A" ? 13 : 7);
    return canvas;
  }

  function save(canvas, name){
    const a = document.createElement("a");
    a.download = name;
    a.href = canvas.toDataURL("image/png");
    a.click();
  }

  return { FORMATS, THEMES, draw, save, mark, lockup, field, grain, vignette, text, wrap, block, hexa, rng };
})();
