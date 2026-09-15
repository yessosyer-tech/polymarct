/* POLYMARCT / motion runtime
   A fixed 1920x1080 stage, a deterministic timeline and a transport bar.
   Deterministic matters: a capture of beat 7.2s is identical every run, so a
   screen recording is repeatable instead of a lucky take.

   Keys:  space play/pause   R restart   H hide the transport   ,/. step 1s
   Query: ?rec=1 clean plate, ?t=6 seek to 6s, ?pause=1 hold that frame. */

const MO = (() => {
  const STAGE_W = 1920, STAGE_H = 1080;

  /* ---------- easing ---------- */
  const E = {
    linear: t => t,
    inQuad: t => t*t,
    outQuad: t => 1-(1-t)*(1-t),
    inOutCubic: t => t<.5 ? 4*t*t*t : 1-Math.pow(-2*t+2,3)/2,
    outExpo: t => t===1 ? 1 : 1-Math.pow(2,-10*t),
    inExpo: t => t===0 ? 0 : Math.pow(2,10*t-10),
    outBack: t => 1+2.2*Math.pow(t-1,3)+1.2*Math.pow(t-1,2),
    outElastic: t => t===0||t===1 ? t : Math.pow(2,-9*t)*Math.sin((t*10-0.75)*(2*Math.PI/3))+1,
    /* a settle that overshoots once and stops, the house easing */
    settle: t => 1-Math.pow(1-t,3)*Math.cos(t*Math.PI*1.1)
  };

  const lerp  = (a,b,t) => a+(b-a)*t;
  const clamp = (v,a,b) => Math.max(a, Math.min(b, v));
  const inv   = (v,a,b) => clamp((v-a)/(b-a), 0, 1);

  /* ---------- timeline ---------- */
  class Timeline {
    constructor(duration){ this.duration = duration; this.beats = []; this.t = 0; }
    /* fn(p, t) where p is the eased 0..1 progress of this beat */
    beat(start, end, fn, ease){ this.beats.push({ start, end, fn, ease: ease || E.linear }); return this; }
    at(time, fn){ this.beats.push({ start:time, end:time+0.0001, fn, ease:E.linear, once:true }); return this; }
    /* Only beats that have started are applied, in order, so a later beat
       never writes its p=0 state over an earlier one. reset() puts the stage
       back to zero first, which makes scrubbing backwards correct too. */
    seek(t){
      this.t = t;
      if (this.reset) this.reset();
      for (const b of this.beats){
        if (t < b.start) continue;
        b.fn(b.ease(inv(t, b.start, b.end)), t, true);
      }
    }
  }

  /* ---------- transport ---------- */
  function mount(opts){
    const { duration, render, title, loop = true, reset } = opts;
    const q = new URLSearchParams(location.search);
    const rec = q.get("rec") === "1";

    const stage = document.getElementById("stage");
    function fit(){
      const s = Math.min(innerWidth/STAGE_W, innerHeight/STAGE_H);
      stage.style.transform = `translate(-50%,-50%) scale(${s})`;
    }
    addEventListener("resize", fit, { passive:true });
    fit();

    const tl = new Timeline(duration);
    tl.reset = reset;
    render(tl);

    const bar = document.createElement("div");
    bar.className = "transport" + (rec ? " gone" : "");
    bar.innerHTML = `
      <button data-a="play">PAUSE</button>
      <button data-a="restart">RESTART</button>
      <div class="scrub"><i></i></div>
      <span class="tc">0.0 / ${duration.toFixed(1)}s</span>
      <span class="hint">${title} // 1920&times;1080 // SPACE R H</span>`;
    document.body.appendChild(bar);
    const fill = bar.querySelector(".scrub i"), tc = bar.querySelector(".tc"), pb = bar.querySelector('[data-a="play"]');

    let playing = q.get("pause") !== "1", t = parseFloat(q.get("t") || "0"), last = performance.now();

    function frame(now){
      const dt = Math.min(0.05, (now-last)/1000); last = now;
      if (playing){
        t += dt;
        if (t > duration){ if (loop) t = 0; else { t = duration; playing = false; pb.textContent = "PLAY"; } }
      }
      tl.seek(t);
      if (!rec){
        fill.style.width = (t/duration*100) + "%";
        tc.textContent = t.toFixed(1) + " / " + duration.toFixed(1) + "s";
      }
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);

    bar.onclick = e => {
      const a = e.target.dataset.a;
      if (a === "play"){ playing = !playing; pb.textContent = playing ? "PAUSE" : "PLAY"; }
      if (a === "restart"){ t = 0; playing = true; pb.textContent = "PAUSE"; }
    };
    bar.querySelector(".scrub").onclick = e => {
      const r = e.currentTarget.getBoundingClientRect();
      t = clamp((e.clientX-r.left)/r.width, 0, 1) * duration;
    };
    addEventListener("keydown", e => {
      if (e.code === "Space"){ e.preventDefault(); playing = !playing; pb.textContent = playing?"PAUSE":"PLAY"; }
      if (e.key === "r" || e.key === "R"){ t = 0; playing = true; }
      if (e.key === "h" || e.key === "H"){ bar.classList.toggle("gone"); }
      if (e.key === ","){ t = clamp(t-1,0,duration); }
      if (e.key === "."){ t = clamp(t+1,0,duration); }
    });

    return { tl, get time(){ return t; } };
  }

  /* ---------- canvas helpers ---------- */
  function hidpi(cv, w = STAGE_W, h = STAGE_H){
    cv.width = w; cv.height = h;
    return cv.getContext("2d");
  }

  function rng(seed){
    let s = 0; for (let i=0;i<seed.length;i++) s = (s*31+seed.charCodeAt(i))>>>0;
    return () => { s^=s<<13; s>>>=0; s^=s>>17; s^=s<<5; s>>>=0; return s/4294967296; };
  }

  /* the market field, as a living layer. speed drives the rush. */
  class Field {
    constructor(w, h, seed, count){
      const r = rng(seed);
      this.w = w; this.h = h;
      this.lines = Array.from({length: count}, () => ({
        x: r()*w, y: r()*h, len: 20+r()*280, v: (0.25+r()*2.4)*(r()>.5?1:-1),
        a: .04+r()*.16, hot: r()>.93, tilt: (r()-.5)*.14
      }));
      this.labels = Array.from({length: Math.round(count/7)}, () => ({
        x: r()*w, y: r()*h, v: (0.2+r()*1.4)*(r()>.5?1:-1), a: .08+r()*.24,
        s: 12+r()*12, hot: r()>.88,
        txt: ["BTC>125K","FED CUT","ARC 1M TX","USDC 30%","+8.4%","-3.1%","67¢","41¢","EARLY","VOL 4.8M","TVL 100M","ETH>5K","DEAD EVEN"][ (r()*13)|0 ]
      }));
    }
    draw(ctx, t, { speed = 1, alpha = 1, blur = 0 } = {}){
      ctx.save(); ctx.globalAlpha = alpha;
      this.lines.forEach(l => {
        let x = l.x + l.v * t * 60 * speed;
        x = ((x % (this.w+600)) + this.w+600) % (this.w+600) - 300;
        const len = l.len * (1 + blur*5);
        ctx.beginPath(); ctx.moveTo(x, l.y); ctx.lineTo(x+len, l.y+len*l.tilt);
        ctx.strokeStyle = l.hot ? `rgba(204,255,0,${l.a*2.2})` : `rgba(242,239,233,${l.a})`;
        ctx.lineWidth = l.hot ? 2 : 1.1;
        ctx.stroke();
      });
      this.labels.forEach(l => {
        let x = l.x + l.v * t * 60 * speed;
        x = ((x % (this.w+600)) + this.w+600) % (this.w+600) - 300;
        ctx.font = `500 ${l.s}px ui-monospace,SFMono-Regular,Menlo,monospace`;
        ctx.fillStyle = l.hot ? `rgba(204,255,0,${l.a+.2})` : `rgba(242,239,233,${l.a})`;
        ctx.fillText(l.txt, x, l.y);
      });
      ctx.restore();
    }
  }

  /* THE SPLIT UNIT, drawn on canvas with a live boundary */
  const EDGE = [[30,6],[30,20],[44,20],[44,32],[22,32],[22,44],[38,44],[38,58]];
  function markPath(shift){
    return EDGE.map(([x,y],i) => [x + (i%2 ? 0 : 0) + shift*((i%4<2)?1:-1)*0.5 + shift, y]);
  }
  function drawMark(ctx, x, y, s, { draw = 1, shift = 0, acid = "#CCFF00", fg = "#F2EFE9", bg = "#08090A", frame = .24 } = {}){
    const u = s/64, pts = markPath(shift);
    ctx.save(); ctx.translate(x,y); ctx.scale(u,u);
    ctx.lineJoin = "miter";
    ctx.strokeStyle = `rgba(242,239,233,${frame})`; ctx.lineWidth = 1.5;
    ctx.strokeRect(6,6,52,52);
    if (draw > 0){
      ctx.save();
      ctx.beginPath(); ctx.rect(0, 0, 64, 6 + 52*draw); ctx.clip();
      ctx.beginPath(); ctx.moveTo(6,6);
      pts.forEach(([px,py])=>ctx.lineTo(px,py));
      ctx.lineTo(6,58); ctx.closePath();
      ctx.fillStyle = fg; ctx.fill();
      ctx.beginPath(); ctx.moveTo(pts[0][0],pts[0][1]);
      pts.slice(1).forEach(([px,py])=>ctx.lineTo(px,py));
      ctx.strokeStyle = acid; ctx.lineWidth = 2.5; ctx.stroke();
      ctx.restore();
    }
    ctx.strokeStyle = "rgba(242,239,233,.42)"; ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(36,13); ctx.lineTo(58,13);
    ctx.moveTo(50,26); ctx.lineTo(58,26);
    ctx.moveTo(28,38); ctx.lineTo(58,38);
    ctx.moveTo(44,51); ctx.lineTo(58,51);
    ctx.stroke();
    if (draw > .7){ ctx.strokeStyle = acid; ctx.lineWidth = 2; ctx.strokeRect(34+shift,40,8,8); }
    ctx.restore();
  }

  /* text with real tracking, tabular figures */
  function text(ctx, str, x, y, { size=40, weight=500, mono=false, track=0, color="#F2EFE9", align="left", alpha=1 } = {}){
    ctx.save(); ctx.globalAlpha = alpha;
    ctx.font = `${weight} ${size}px ${mono ? "'JetBrains Mono',ui-monospace,Menlo,monospace" : "'Inter Tight','Inter',Helvetica,Arial,sans-serif"}`;
    if ("letterSpacing" in ctx) ctx.letterSpacing = track + "px";
    ctx.fillStyle = color; ctx.textAlign = align;
    ctx.fillText(str, x, y);
    const w = ctx.measureText(str).width;
    ctx.restore();
    return w;
  }

  /* a number that counts, with a digit jitter on the way */
  function counter(v, decimals, jitter){
    const n = jitter ? v + (Math.random()-.5)*jitter : v;
    return n.toFixed(decimals);
  }

  return { STAGE_W, STAGE_H, E, lerp, clamp, inv, Timeline, mount, hidpi, rng, Field, drawMark, text, counter, markPath };
})();
