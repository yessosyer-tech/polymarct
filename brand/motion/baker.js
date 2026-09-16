/* POLYMARCT / DOM baker
   Films 01 to 03 draw their spectacle on canvas and their type in the DOM,
   which a canvas capture cannot see. Rather than rewriting three films, this
   reads the laid-out DOM every frame and paints the same text onto the output
   canvas: real positions, real fonts, real line breaks, honouring opacity,
   letter-spacing, text-transform and the clip-path wipes the films use.

   BAKE.compose(out, { canvases, root, treatment }) -> one finished frame. */

const BAKE = (() => {

  function stageRect(root){
    /* the stage is transformed to fit the viewport; undo that scale so every
       measurement lands back in the film's own 1920x1080 space */
    const r = root.getBoundingClientRect();
    const scale = r.width / root.offsetWidth || 1;
    return { left: r.left, top: r.top, scale };
  }

  /* split a text node into its visual lines, so wrapped copy bakes correctly.
     Each line is measured as its own range, so the left edge is the real start
     of the line rather than wherever the break happened to fall. */
  function lines(node){
    const txt = node.nodeValue;
    if (!txt || !txt.trim()) return [];
    const range = document.createRange();
    const rectOf = (a, b) => { range.setStart(node, a); range.setEnd(node, b); return range.getBoundingClientRect(); };
    const out = [];
    let start = 0, prevTop = null;
    for (let i = 1; i <= txt.length; i++){
      const r = rectOf(i - 1, i);
      if (r.width === 0 && r.height === 0) continue;
      if (prevTop === null) prevTop = r.top;
      if (Math.abs(r.top - prevTop) > 1){
        out.push({ text: txt.slice(start, i - 1), rect: rectOf(start, i - 1) });
        start = i - 1;
        prevTop = r.top;
      }
    }
    out.push({ text: txt.slice(start), rect: rectOf(start, txt.length) });
    return out.filter(l => l.text.trim() && l.rect && l.rect.width > 0);
  }

  function clipInset(el, s){
    /* the films reveal type with clip-path inset(); reproduce it as a canvas clip */
    const cp = getComputedStyle(el).clipPath;
    if (!cp || cp === "none" || !cp.startsWith("inset")) return null;
    const nums = cp.match(/-?[\d.]+/g);
    if (!nums) return null;
    const r = el.getBoundingClientRect();
    const isPct = cp.includes("%");
    const v = nums.map(Number);
    const [top, right, bottom, left] = v.length >= 4 ? v : [v[0], v[1] === undefined ? v[0] : v[1], v[0], v[1] === undefined ? v[0] : v[1]];
    const w = r.width, h = r.height;
    const px = (n, base) => isPct ? base * n/100 : n;
    return {
      x: (r.left - s.left)/s.scale + px(left, w)/s.scale,
      y: (r.top - s.top)/s.scale + px(top, h)/s.scale,
      w: (w - px(left, w) - px(right, w))/s.scale,
      h: (h - px(top, h) - px(bottom, h))/s.scale
    };
  }

  function effectiveOpacity(el, root){
    let o = 1, n = el;
    while (n && n !== root.parentNode){
      const cs = getComputedStyle(n);
      if (cs.display === "none" || cs.visibility === "hidden") return 0;
      o *= parseFloat(cs.opacity);
      if (o <= 0.004) return 0;
      n = n.parentElement;
    }
    return o;
  }

  function bakeText(ctx, root){
    const s = stageRect(root);
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: n => n.nodeValue && n.nodeValue.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT
    });
    const seen = [];
    let node;
    while ((node = walker.nextNode())) seen.push(node);

    for (const n of seen){
      const el = n.parentElement;
      if (!el || el.closest("canvas")) continue;
      const alpha = effectiveOpacity(el, root);
      if (alpha <= 0.004) continue;
      const cs = getComputedStyle(el);
      const fs = parseFloat(cs.fontSize);
      if (!fs) continue;

      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.fillStyle = cs.color;
      ctx.font = `${cs.fontStyle} ${cs.fontWeight} ${fs}px ${cs.fontFamily}`;
      const ls = parseFloat(cs.letterSpacing);
      if ("letterSpacing" in ctx) ctx.letterSpacing = (isNaN(ls) ? 0 : ls) + "px";
      ctx.textBaseline = "alphabetic";
      ctx.textAlign = "left";

      const clip = clipInset(el, s);
      if (clip){ ctx.beginPath(); ctx.rect(clip.x, clip.y, clip.w, clip.h); ctx.clip(); }

      for (const line of lines(n)){
        const r = line.rect;
        const x = (r.left - s.left) / s.scale;
        /* alphabetic baseline sits near the bottom of the line box */
        const y = (r.bottom - s.top) / s.scale - (r.height / s.scale) * 0.21;
        let text = line.text;
        const tt = cs.textTransform;
        if (tt === "uppercase") text = text.toUpperCase();
        else if (tt === "lowercase") text = text.toLowerCase();
        ctx.fillText(text.trim(), x, y);
      }
      ctx.restore();
    }
  }

  /* boxes the films draw with CSS: bars, rules, panels, chips */
  function bakeBoxes(ctx, root){
    const s = stageRect(root);
    const els = root.querySelectorAll(".bar, .bar i, .rule, .panel, .card, .leg, .chip, .legrow div, .themebar .tr, .themebar .tr i, .btn, .stamp, .depth, .feed .row, .ev");
    for (const el of els){
      const alpha = effectiveOpacity(el, root);
      if (alpha <= 0.004) continue;
      const cs = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) continue;
      const x = (r.left - s.left)/s.scale, y = (r.top - s.top)/s.scale;
      const w = r.width/s.scale, h = r.height/s.scale;
      ctx.save();
      ctx.globalAlpha = alpha;
      const bgc = cs.backgroundColor;
      if (bgc && bgc !== "rgba(0, 0, 0, 0)" && bgc !== "transparent"){
        if (cs.boxShadow && cs.boxShadow !== "none"){
          ctx.shadowColor = "rgba(0,0,0,.72)"; ctx.shadowBlur = 70; ctx.shadowOffsetY = 26;
        }
        ctx.fillStyle = bgc; ctx.fillRect(x, y, w, h);
        ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;
      }
      const bw = parseFloat(cs.borderTopWidth);
      if (bw > 0 && cs.borderTopColor !== "rgba(0, 0, 0, 0)"){
        ctx.strokeStyle = cs.borderTopColor; ctx.lineWidth = bw;
        ctx.strokeRect(x, y, w, h);
      } else {
        const bbw = parseFloat(cs.borderBottomWidth);
        if (bbw > 0 && cs.borderBottomColor !== "rgba(0, 0, 0, 0)"){
          ctx.strokeStyle = cs.borderBottomColor; ctx.lineWidth = bbw;
          ctx.beginPath(); ctx.moveTo(x, y+h); ctx.lineTo(x+w, y+h); ctx.stroke();
        }
      }
      ctx.restore();
    }
  }

  /* film treatment, matching the CSS layers the films show on screen */
  const NOISE = (() => {
    const c = document.createElement("canvas"); c.width = c.height = 256;
    const x = c.getContext("2d"), img = x.createImageData(256,256), d = img.data;
    for (let i=0;i<d.length;i+=4){ const v = 128 + (Math.random()-.5)*255; d[i]=d[i+1]=d[i+2]=v; d[i+3]=255; }
    x.putImageData(img,0,0); return c;
  })();
  const SCAN = (() => {
    const c = document.createElement("canvas"); c.width = 4; c.height = 4;
    const x = c.getContext("2d"); x.fillStyle = "rgba(242,239,233,.075)"; x.fillRect(0,0,4,1); return c;
  })();
  let VIG = null;
  function treatment(ctx, w, h){
    if (!VIG){
      VIG = ctx.createRadialGradient(w/2,h/2,w*0.16, w/2,h/2,w*0.62);
      VIG.addColorStop(0,"rgba(0,0,0,0)"); VIG.addColorStop(1,"rgba(0,0,0,.72)");
    }
    ctx.save();
    ctx.globalAlpha = .16;
    ctx.fillStyle = ctx.createPattern(SCAN, "repeat"); ctx.fillRect(0,0,w,h);
    ctx.globalAlpha = .07; ctx.globalCompositeOperation = "overlay";
    const ox = (Math.random()*256)|0, oy = (Math.random()*256)|0;
    for (let x=-ox;x<w;x+=256) for (let y=-oy;y<h;y+=256) ctx.drawImage(NOISE, x, y);
    ctx.globalCompositeOperation = "source-over"; ctx.globalAlpha = 1;
    ctx.fillStyle = VIG; ctx.fillRect(0,0,w,h);
    ctx.restore();
  }

  function compose(out, opts){
    const root = opts.root;
    /* bake at 1:1. The stage is normally scaled to fit the viewport, and a
       scaled stage means every measurement needs unpicking; this removes the
       problem instead of compensating for it. */
    const prev = root.style.transform;
    root.style.transform = "none";
    const ctx = out.getContext("2d");
    ctx.fillStyle = "#08090A";
    ctx.fillRect(0,0,out.width,out.height);
    /* every canvas in the stage, at its own laid-out position: full bleed
       layers, the probability chart, the index dial, all of them */
    const s = stageRect(root);
    root.querySelectorAll("canvas").forEach(c => {
      if (effectiveOpacity(c, root) <= 0.004) return;
      const r = c.getBoundingClientRect();
      if (!r.width || !r.height) return;
      ctx.save();
      ctx.globalAlpha = effectiveOpacity(c, root);
      ctx.drawImage(c, (r.left - s.left)/s.scale, (r.top - s.top)/s.scale, r.width/s.scale, r.height/s.scale);
      ctx.restore();
    });
    bakeBoxes(ctx, opts.root);
    bakeText(ctx, opts.root);
    if (opts.treatment !== false) treatment(ctx, out.width, out.height);
    root.style.transform = prev;
    return out;
  }

  return { compose, bakeText, bakeBoxes, treatment };
})();
