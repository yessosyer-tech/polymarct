/* POLYMARCT / TICK
   ============================================================
   The mascot is not decoration bolted onto the brand, it is the brand's own
   acid bar stood up and given a face. In the mark, that bar is the last price
   sitting in the gap between the two sides of the book. TICK is that bar: the
   smallest movement a price can make, which is exactly what a tick is.

   Rules that keep him consistent, forever:
     - body is always acid #CCFF00, never recoloured
     - visor is always graphite, eyes are always warm white
     - arms and the tick on his head are warm white
     - he floats. He has no legs, because a price does not walk
     - he points at real things and never blocks the number he is pointing at

   Everything is drawn procedurally from one function, so every still and every
   frame of every film comes from the same character rather than a redrawing
   of him.

     MASCOT.draw(ctx, { x, y, s, pose, dir, expr, tick, t })

   x,y is his centre, s is his height in pixels. Poses: idle, point, cheer,
   think, confused, hold, press. dir: left, right, up, down.
   ============================================================ */

const MASCOT = (() => {
  const ACID = "#CCFF00", WHITE = "#F2EFE9", BLACK = "#08090A", NO = "#FF4D2E";

  function rr(c, x, y, w, h, r){
    c.beginPath();
    c.moveTo(x + r, y);
    c.lineTo(x + w - r, y); c.quadraticCurveTo(x + w, y, x + w, y + r);
    c.lineTo(x + w, y + h - r); c.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    c.lineTo(x + r, y + h); c.quadraticCurveTo(x, y + h, x, y + h - r);
    c.lineTo(x, y + r); c.quadraticCurveTo(x, y, x + r, y);
    c.closePath();
  }

  /* ---- the face. Every expression is the same two eyes, moved. ---- */
  function eyes(c, expr, w, h, blink){
    const ew = w * 0.17, gap = w * 0.20;
    const cx = -gap / 2 - ew / 2, cx2 = gap / 2 + ew / 2;
    c.fillStyle = WHITE;
    c.strokeStyle = WHITE;
    c.lineCap = "round";
    c.lineJoin = "round";

    if (blink){
      c.lineWidth = h * 0.09;
      [cx, cx2].forEach(x => { c.beginPath(); c.moveTo(x - ew/2, 0); c.lineTo(x + ew/2, 0); c.stroke(); });
      return;
    }
    switch (expr){
      case "happy":                              // two upward arcs
        c.lineWidth = h * 0.10;
        [cx, cx2].forEach(x => {
          c.beginPath();
          c.moveTo(x - ew/2, ew*0.32); c.quadraticCurveTo(x, -ew*0.42, x + ew/2, ew*0.32);
          c.stroke();
        });
        break;
      case "focus":                              // narrow slits, reading the tape
        [cx, cx2].forEach(x => c.fillRect(x - ew/2, -ew*0.12, ew, ew*0.26));
        break;
      case "wide":                               // caught by a move
        [cx, cx2].forEach(x => {
          c.beginPath(); c.arc(x, 0, ew*0.60, 0, 7); c.fill();
          c.fillStyle = BLACK; c.beginPath(); c.arc(x, 0, ew*0.22, 0, 7); c.fill();
          c.fillStyle = WHITE;
        });
        break;
      case "confused":                           // one of each, the 51/49 face
        c.fillRect(cx - ew/2, -ew/2, ew, ew);
        c.beginPath(); c.arc(cx2, 0, ew*0.52, 0, 7); c.fill();
        break;
      default:                                   // neutral, two squares
        [cx, cx2].forEach(x => c.fillRect(x - ew/2, -ew/2, ew, ew));
    }
  }

  /* ---- the tick on his head: which way the market went ---- */
  function headTick(c, dirTick, w, h){
    const s = w * 0.22;
    c.strokeStyle = dirTick === "down" ? NO : WHITE;
    c.lineWidth = h * 0.045;
    c.lineCap = "round"; c.lineJoin = "round";
    c.beginPath();
    if (dirTick === "down"){ c.moveTo(-s, -s*0.5); c.lineTo(0, s*0.5); c.lineTo(s, -s*0.5); }
    else if (dirTick === "flat"){ c.moveTo(-s, 0); c.lineTo(s, 0); }
    else { c.moveTo(-s, s*0.5); c.lineTo(0, -s*0.5); c.lineTo(s, s*0.5); }
    c.stroke();
  }

  /* ---- an arm: shoulder, elbow, hand. Angles in radians. ---- */
  function arm(c, side, a1, a2, w, h, hand){
    const sx = side * w * 0.5, sy = -h * 0.06;
    const up = h * 0.165, fo = h * 0.145;
    const ex = sx + Math.cos(a1) * up * side, ey = sy + Math.sin(a1) * up;
    const hx = ex + Math.cos(a2) * fo * side, hy = ey + Math.sin(a2) * fo;
    c.strokeStyle = WHITE;
    c.lineWidth = h * 0.05;
    c.lineCap = "round"; c.lineJoin = "round";
    c.beginPath(); c.moveTo(sx, sy); c.lineTo(ex, ey); c.lineTo(hx, hy); c.stroke();
    c.fillStyle = WHITE;
    if (hand === "point"){
      // a small square hand with one finger, aimed along the forearm
      const ang = Math.atan2(hy - ey, hx - ex);
      c.save(); c.translate(hx, hy); c.rotate(ang);
      c.fillRect(-h*0.035, -h*0.035, h*0.07, h*0.07);
      c.fillRect(h*0.02, -h*0.012, h*0.085, h*0.024);
      c.restore();
    } else {
      c.beginPath(); c.arc(hx, hy, h*0.037, 0, 7); c.fill();
    }
    return { hx, hy };
  }

  const POSES = {
    /* [leftShoulder, leftForearm, rightShoulder, rightForearm, leftHand, rightHand] */
    idle:     [0.55, 0.75, 0.55, 0.75, "round", "round"],
    think:    [0.7, 1.0, -0.35, -1.25, "round", "round"],
    cheer:    [-1.15, -1.5, -1.15, -1.5, "round", "round"],
    hold:     [0.15, -0.35, 0.15, -0.35, "round", "round"],
    press:    [0.6, 0.85, -0.25, 0.25, "round", "point"],
    confused: [0.6, 1.15, -0.5, -0.9, "round", "round"],
  };

  function draw(c, o){
    const s = o.s || 120;
    const w = s * 0.62, h = s;
    const t = o.t || 0;
    const float = Math.sin(t * 1.8) * s * 0.022;          // he hovers, always
    const x = o.x, y = (o.y || 0) + float;
    const pose = o.pose || "idle";
    const dir = o.dir || "right";
    const expr = o.expr || "neutral";
    const blink = o.blink !== undefined ? o.blink
      : (Math.sin(t * 0.9) > 0.985 || Math.sin(t * 2.3 + 1.7) > 0.992);

    c.save();
    c.translate(x, y);
    if (o.tiltDeg) c.rotate(o.tiltDeg * Math.PI / 180);

    /* the shadow he casts, so he sits in the frame rather than on it */
    if (o.shadow !== false){
      c.save();
      c.globalAlpha = 0.34 - Math.abs(float) / (s * 0.09) * 0.10;
      c.fillStyle = "#000";
      c.beginPath();
      c.ellipse(0, h * 0.62, w * 0.44, h * 0.045, 0, 0, 7);
      c.fill();
      c.restore();
    }

    /* body */
    c.fillStyle = ACID;
    rr(c, -w/2, -h/2, w, h * 0.86, w * 0.16);
    c.fill();

    /* the head tick */
    c.save();
    c.translate(0, -h * 0.5 - h * 0.10);
    headTick(c, o.tick || "up", w, h);
    c.restore();

    /* visor */
    const vw = w * 0.78, vh = h * 0.26, vy = -h * 0.30;
    c.fillStyle = BLACK;
    rr(c, -vw/2, vy, vw, vh, vh * 0.30);
    c.fill();

    /* eyes, offset toward whatever he is looking at */
    const look = dir === "left" ? -w * 0.07 : dir === "right" ? w * 0.07 : 0;
    const lookY = dir === "up" ? -vh * 0.12 : dir === "down" ? vh * 0.12 : 0;
    c.save();
    c.translate(look, vy + vh/2 + lookY);
    eyes(c, expr, w, h, blink);
    c.restore();

    /* a readout under the visor, when he is carrying a number */
    if (o.label){
      c.save();
      c.fillStyle = BLACK;
      c.font = `700 ${h * 0.115}px 'JetBrains Mono',ui-monospace,monospace`;
      c.textAlign = "center"; c.textBaseline = "middle";
      if ("letterSpacing" in c) c.letterSpacing = "0px";
      c.fillText(o.label, 0, h * 0.06);
      c.restore();
    }

    /* arms */
    const p = POSES[pose] || POSES.idle;
    const swing = pose === "idle" ? Math.sin(t * 1.8 + 0.6) * 0.10 : 0;
    const mirror = dir === "left" ? -1 : 1;
    if (pose === "point"){
      // one arm points where he is looking, the other rests
      const a = dir === "up" ? -1.35 : dir === "down" ? 1.15 : -0.12;
      arm(c, -mirror, 0.55, 0.8, w, h, "round");
      const hand = arm(c, mirror, a, a, w, h, "point");
      c.restore();
      return hand;
    }
    arm(c, -1, p[0] + swing, p[1] + swing, w, h, p[4]);
    arm(c,  1, p[2] - swing, p[3] - swing, w, h, p[5]);

    c.restore();
    return null;
  }

  /* A dashed leader from his hand to the thing he is talking about. Drawn
     separately so it can sit under the UI he is pointing at. */
  function pointerLine(c, from, to, dash){
    c.save();
    c.strokeStyle = "rgba(204,255,0,.75)";
    c.lineWidth = 2.5;
    c.setLineDash(dash === false ? [] : [9, 7]);
    c.beginPath();
    c.moveTo(from.x, from.y);
    const mx = (from.x + to.x) / 2;
    c.bezierCurveTo(mx, from.y, mx, to.y, to.x, to.y);
    c.stroke();
    c.setLineDash([]);
    c.beginPath(); c.arc(to.x, to.y, 5, 0, 7);
    c.fillStyle = ACID; c.fill();
    c.restore();
  }

  /* A speech line in his voice: flat, short, never an exclamation mark. */
  function speech(c, text, x, y, size, align){
    c.save();
    c.font = `600 ${size}px 'Inter Tight',Inter,sans-serif`;
    c.textAlign = align || "left";
    if ("letterSpacing" in c) c.letterSpacing = (-size * 0.02) + "px";
    c.fillStyle = WHITE;
    c.fillText(text, x, y);
    c.restore();
  }

  return { draw, pointerLine, speech, ACID, WHITE, BLACK, NO, POSES };
})();
