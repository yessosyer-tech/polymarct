"""TICK, the Polymarct mascot. Drawn in Python, rendered straight to pixels.

He is the acid bar from the mark, stood up: a machined object rather than a
flat shape. Chassis, plate, seams, an inset visor with lit eyes, a live price
tape across his chest, a feed probe and articulated arms with real joints.

This module is the single source of the character. Cards and films both call
draw(), so he cannot drift between them.

    from tick import draw
    draw(img, x=800, y=500, s=320, pose="point", dir="left", expr="focus")

Colours are locked and must never change:
    plate      #CCFF00     the acid body, he is the price
    plate low  #9FCC00     the shaded lower third
    chassis    #14171A     the housing behind the plate
    visor      #05070A     the inset window
    detail     #F2EFE9     eyes, arms, rim light
    data       #2F6BFF     the one blue accent, used only on the tape
"""
import math
from PIL import Image, ImageDraw, ImageFilter

PLATE = (204, 255, 0)
PLATE_LO = (159, 204, 0)
PLATE_HI = (226, 255, 110)
CHASSIS = (20, 23, 26)
VISOR = (5, 7, 10)
DETAIL = (242, 239, 233)
DATA = (47, 107, 255)
RED = (255, 77, 46)

POSES = {
    # left shoulder, left elbow, right shoulder, right elbow (radians)
    "idle":     (0.62, 0.42, 0.62, 0.42),
    "point":    (0.62, 0.42, -0.05, -0.02),
    "think":    (0.75, 0.55, -0.55, -1.15),
    "cheer":    (-1.05, -0.65, -1.05, -0.65),
    "hold":     (0.10, -0.42, 0.10, -0.42),
    "press":    (0.66, 0.46, -0.18, 0.28),
    "confused": (0.70, 0.62, -0.42, -0.85),
}


def _rr(d, box, r, **kw):
    d.rounded_rectangle(box, radius=r, **kw)


def _glow(size, paint, blur, alpha=255):
    """Paint something on its own layer and blur it, for emissive parts."""
    lay = Image.new("RGBA", size, (0, 0, 0, 0))
    paint(ImageDraw.Draw(lay))
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    if alpha < 255:
        a = lay.getchannel("A").point(lambda v: int(v * alpha / 255))
        lay.putalpha(a)
    return lay


def _eyes(d, cx, cy, w, h, expr, blink, col=DETAIL):
    ew, eh = w * 0.175, h * 0.052
    gap = w * 0.175
    lx, rx = cx - gap / 2 - ew / 2, cx + gap / 2 + ew / 2

    if blink:
        for x in (lx, rx):
            _rr(d, [x - ew / 2, cy - eh * 0.28, x + ew / 2, cy + eh * 0.28], eh * 0.28, fill=col)
        return

    if expr == "happy":
        wdt = max(2, int(h * 0.022))
        for x in (lx, rx):
            d.arc([x - ew / 2, cy - eh * 0.9, x + ew / 2, cy + eh * 1.1],
                  200, 340, fill=col, width=wdt)
    elif expr == "focus":
        for x in (lx, rx):
            _rr(d, [x - ew / 2, cy - eh * 0.30, x + ew / 2, cy + eh * 0.30], eh * 0.30, fill=col)
    elif expr == "wide":
        for x in (lx, rx):
            d.ellipse([x - ew * 0.60, cy - ew * 0.60, x + ew * 0.60, cy + ew * 0.60], fill=col)
            d.ellipse([x - ew * 0.20, cy - ew * 0.20, x + ew * 0.20, cy + ew * 0.20], fill=VISOR)
    elif expr == "confused":
        _rr(d, [lx - ew / 2, cy - eh, lx + ew / 2, cy + eh], eh * 0.35, fill=col)
        d.ellipse([rx - ew * 0.52, cy - ew * 0.52, rx + ew * 0.52, cy + ew * 0.52], fill=col)
    else:
        for x in (lx, rx):
            _rr(d, [x - ew / 2, cy - eh, x + ew / 2, cy + eh], eh * 0.35, fill=col)


def _arm(d, ox, oy, side, a1, a2, w, h, hand):
    """Three segments with joint pucks, tapering out to a gripper."""
    sx = ox + side * w * 0.46
    sy = oy - h * 0.04
    up, fo = h * 0.175, h * 0.150
    ex = sx + math.cos(a1) * up * side
    ey = sy + math.sin(a1) * up
    hx = ex + math.cos(a2) * fo * side
    hy = ey + math.sin(a2) * fo

    d.line([sx, sy, ex, ey], fill=DETAIL, width=max(2, int(h * 0.048)))
    d.line([ex, ey, hx, hy], fill=DETAIL, width=max(2, int(h * 0.038)))
    for (jx, jy, r) in ((sx, sy, h * 0.036), (ex, ey, h * 0.028)):
        d.ellipse([jx - r, jy - r, jx + r, jy + r], fill=CHASSIS, outline=DETAIL,
                  width=max(1, int(h * 0.012)))

    ang = math.atan2(hy - ey, hx - ex)
    if hand == "point":
        g = h * 0.034
        d.ellipse([hx - g, hy - g, hx + g, hy + g], fill=DETAIL)
        fx, fy = hx + math.cos(ang) * h * 0.085, hy + math.sin(ang) * h * 0.085
        d.line([hx, hy, fx, fy], fill=DETAIL, width=max(2, int(h * 0.022)))
        return (fx, fy)
    g = h * 0.038
    d.ellipse([hx - g, hy - g, hx + g, hy + g], fill=DETAIL)
    d.ellipse([hx - g * 0.42, hy - g * 0.42, hx + g * 0.42, hy + g * 0.42], fill=CHASSIS)
    return (hx, hy)


def draw(img, x, y, s, pose="idle", dir="right", expr="neutral", tick="up",
         label=None, t=0.0, blink=None, shadow=True, tape=True):
    """Draw TICK centred on (x, y) at height s onto an RGB/RGBA image.

    Returns the hand position, so a pointer line can start where he points.
    """
    w, h = s * 0.62, s
    y = y + math.sin(t * 1.8) * s * 0.018            # he hovers, always
    if blink is None:
        blink = math.sin(t * 0.9) > 0.985 or math.sin(t * 2.3 + 1.7) > 0.992

    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)

    left, top = x - w / 2, y - h / 2
    bh = h * 0.86                                     # plate height

    # contact shadow, soft
    if shadow:
        sh = _glow(img.size, lambda dd: dd.ellipse(
            [x - w * 0.46, y + bh * 0.52, x + w * 0.46, y + bh * 0.60],
            fill=(0, 0, 0, 190)), s * 0.035)
        img.alpha_composite(sh) if img.mode == "RGBA" else img.paste(
            Image.alpha_composite(img.convert("RGBA"), sh).convert(img.mode), (0, 0))

    # chassis: a machined housing peeking out behind the plate
    _rr(d, [left - w * 0.055, top - h * 0.018, left + w + w * 0.055, top + bh + h * 0.030],
        w * 0.20, fill=CHASSIS)

    # the plate itself
    _rr(d, [left, top, left + w, top + bh], w * 0.165, fill=PLATE)
    # shaded lower third, so he has weight
    lo = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lo)
    _rr(ld, [left, top + bh * 0.62, left + w, top + bh], w * 0.165, fill=PLATE_LO + (255,))
    ld.rectangle([left, top + bh * 0.62, left + w, top + bh * 0.72], fill=PLATE_LO + (255,))
    mask = Image.new("L", img.size, 0)
    _rr(ImageDraw.Draw(mask), [left, top, left + w, top + bh], w * 0.165, fill=255)
    lay.paste(lo, (0, 0), Image.composite(lo.getchannel("A"), Image.new("L", img.size, 0), mask))
    d = ImageDraw.Draw(lay)

    # rim light along the top edge
    _rr(d, [left + w * 0.10, top + h * 0.012, left + w * 0.90, top + h * 0.030],
        h * 0.010, fill=PLATE_HI)

    # panel seams
    for fy in (0.50, 0.58):
        d.line([left + w * 0.10, top + bh * fy, left + w * 0.90, top + bh * fy],
               fill=CHASSIS, width=max(1, int(h * 0.007)))

    # visor housing, inset with a lip
    vw, vh = w * 0.80, h * 0.235
    vx, vy = x - vw / 2, top + h * 0.115
    _rr(d, [vx - h * 0.010, vy - h * 0.010, vx + vw + h * 0.010, vy + vh + h * 0.010],
        vh * 0.36, fill=CHASSIS)
    _rr(d, [vx, vy, vx + vw, vy + vh], vh * 0.32, fill=VISOR)
    d.line([vx + vw * 0.12, vy + h * 0.012, vx + vw * 0.88, vy + h * 0.012],
           fill=(90, 96, 100), width=max(1, int(h * 0.008)))

    # eyes, lit: a blurred copy behind the crisp one
    look = {"left": -w * 0.065, "right": w * 0.065}.get(dir, 0)
    lookY = {"up": -vh * 0.10, "down": vh * 0.10}.get(dir, 0)
    ecx, ecy = x + look, vy + vh / 2 + lookY
    bloom = _glow(img.size,
                  lambda dd: _eyes(dd, ecx, ecy, w, h, expr, blink, col=PLATE),
                  s * 0.020, alpha=150)
    lay.alpha_composite(bloom)
    d = ImageDraw.Draw(lay)
    _eyes(d, ecx, ecy, w, h, expr, blink)

    # the price tape across his chest. When he is carrying a number it goes
    # here, in the readout, rather than floating loose over a panel seam.
    if tape:
        tw, th = w * 0.74, h * 0.115
        tx, ty = x - tw / 2, top + bh * 0.68
        _rr(d, [tx, ty, tx + tw, ty + th], th * 0.26, fill=VISOR)
        if label:
            from PIL import ImageFont
            try:
                f = ImageFont.truetype(r"C:\Windows\Fonts\consolab.ttf", int(th * 0.62))
            except OSError:
                f = ImageFont.load_default()
            d.text((x, ty + th * 0.52), str(label), font=f, fill=PLATE, anchor="mm")
        else:
            pts = []
            for i in range(11):
                fx = tx + tw * 0.06 + (tw * 0.52) * i / 10
                fy = ty + th * 0.72 - th * 0.44 * (0.5 + 0.5 * math.sin(i * 0.9 + t * 1.6))
                pts.append((fx, fy))
            d.line(pts, fill=PLATE, width=max(1, int(h * 0.010)))
            d.ellipse([pts[-1][0] - h * 0.010, pts[-1][1] - h * 0.010,
                       pts[-1][0] + h * 0.010, pts[-1][1] + h * 0.010], fill=PLATE)
            dot = th * 0.16
            d.ellipse([tx + tw - dot * 3.2, ty + th / 2 - dot, tx + tw - dot * 1.2, ty + th / 2 + dot],
                      fill=DATA)

    # the head tick, emissive
    tkw = w * 0.24
    ty0 = top - h * 0.055
    col = RED if tick == "down" else DETAIL

    def paint_tick(dd):
        if tick == "down":
            dd.line([x - tkw, ty0 - tkw * 0.45, x, ty0 + tkw * 0.45, x + tkw, ty0 - tkw * 0.45],
                    fill=col, width=max(2, int(h * 0.045)), joint="curve")
        elif tick == "flat":
            dd.line([x - tkw, ty0, x + tkw, ty0], fill=col, width=max(2, int(h * 0.045)))
        else:
            dd.line([x - tkw, ty0 + tkw * 0.45, x, ty0 - tkw * 0.45, x + tkw, ty0 + tkw * 0.45],
                    fill=col, width=max(2, int(h * 0.045)), joint="curve")

    lay.alpha_composite(_glow(img.size, paint_tick, s * 0.022, alpha=120))
    d = ImageDraw.Draw(lay)
    paint_tick(d)

    # feed probe: a thin stalk with a live dot
    px0 = x + w * 0.30
    d.line([px0, top - h * 0.020, px0 + w * 0.10, top - h * 0.150],
           fill=DETAIL, width=max(1, int(h * 0.014)))
    pr = h * 0.026
    lay.alpha_composite(_glow(img.size, lambda dd: dd.ellipse(
        [px0 + w * 0.10 - pr, top - h * 0.150 - pr, px0 + w * 0.10 + pr, top - h * 0.150 + pr],
        fill=PLATE + (255,)), s * 0.020, alpha=170))
    d = ImageDraw.Draw(lay)
    d.ellipse([px0 + w * 0.10 - pr * 0.6, top - h * 0.150 - pr * 0.6,
               px0 + w * 0.10 + pr * 0.6, top - h * 0.150 + pr * 0.6], fill=PLATE)

    # arms last, over the plate
    a = POSES.get(pose, POSES["idle"])
    swing = math.sin(t * 1.8 + 0.6) * 0.09 if pose == "idle" else 0.0
    mirror = -1 if dir == "left" else 1
    hand = None
    if pose == "point":
        aim = {"up": -1.30, "down": 1.10}.get(dir, -0.05)
        _arm(d, x, y, -mirror, 0.62, 0.42, w, h, "round")
        hand = _arm(d, x, y, mirror, aim, aim, w, h, "point")
    else:
        _arm(d, x, y, -1, a[0] + swing, a[1] + swing, w, h, "round")
        _arm(d, x, y, 1, a[2] - swing, a[3] - swing, w, h, "round")

    if img.mode == "RGBA":
        img.alpha_composite(lay)
    else:
        img.paste(Image.alpha_composite(img.convert("RGBA"), lay).convert(img.mode), (0, 0))
    return hand


def pointer(img, frm, to, dash=14, gap=10):
    """A dashed acid leader from his hand to the thing he is talking about."""
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x1, y1 = frm
    x2, y2 = to
    mx = (x1 + x2) / 2
    pts = []
    for i in range(61):
        u = i / 60
        bx = (1 - u) ** 3 * x1 + 3 * (1 - u) ** 2 * u * mx + 3 * (1 - u) * u * u * mx + u ** 3 * x2
        by = (1 - u) ** 3 * y1 + 3 * (1 - u) ** 2 * u * y1 + 3 * (1 - u) * u * u * y2 + u ** 3 * y2
        pts.append((bx, by))
    run = 0.0
    for i in range(len(pts) - 1):
        seg = math.dist(pts[i], pts[i + 1])
        if (run // (dash + gap)) % 1 == 0 and (run % (dash + gap)) < dash:
            d.line([pts[i], pts[i + 1]], fill=PLATE + (200,), width=3)
        run += seg
    r = 6
    d.ellipse([x2 - r, y2 - r, x2 + r, y2 + r], fill=PLATE + (255,))
    if img.mode == "RGBA":
        img.alpha_composite(lay)
    else:
        img.paste(Image.alpha_composite(img.convert("RGBA"), lay).convert(img.mode), (0, 0))
