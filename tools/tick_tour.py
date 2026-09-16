"""THE TOUR. TICK opens the real site and walks you through it.

    python tools/shots.py           photograph the site first
    python tools/tick_tour.py       render, 38s, straight to MP4
    python tools/tick_tour.py --preview   ten frames, to check framing

Every page you see is a real capture of the real site, panned and pushed in.
Nothing is a mock up. TICK stands in front of it and points at the actual
pixels. Pillow draws the frames, a stdlib synth writes the score, ffmpeg muxes.
No browser in the render, no HTML, no capture pass.

Effects: CRT power on, chromatic split, glitch slicing, scanlines, bloom on
acid, a real cursor that clicks real buttons, whip transitions, speed ramps.
Every label and TICK himself are box checked per beat, so nothing overlaps.
"""
import os
import sys
import math
import wave
import struct
import shutil
import random
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import tick as TICK

W, H, FPS, DUR = 1920, 1080, 30, 38.0
OUT = os.path.join(ROOT, "dist", "polymarct-06-tour-1080p.mp4")
TMP = os.path.join(HERE, "_tour")
SHOTS = os.path.join(HERE, "_shots")

BG = (8, 9, 10)
WHITE = (242, 239, 233)
ACID = (204, 255, 0)
DIM = (138, 143, 148)
LINE2 = (58, 62, 66)

FONTS = {}
PAGES = {}
VIGNETTE = None
OVERLAPS = []


def F(size, mono=False):
    k = (size, mono)
    if k not in FONTS:
        p = os.path.join(r"C:\Windows\Fonts", "consolab.ttf" if mono else "segoeuib.ttf")
        FONTS[k] = ImageFont.truetype(p, size) if os.path.exists(p) else ImageFont.load_default()
    return FONTS[k]


def page(name):
    if name not in PAGES:
        PAGES[name] = Image.open(os.path.join(SHOTS, name + ".png")).convert("RGB")
    return PAGES[name]


# ---------------------------------------------------------------- easing
def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def inv(v, a, b):
    return clamp((v - a) / (b - a))


def out_expo(t):
    return 1 - pow(2, -10 * t) if t < 1 else 1


def in_out(t):
    return 4 * t * t * t if t < .5 else 1 - pow(-2 * t + 2, 3) / 2


def lerp(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------- the browser
def viewport(img, name, scroll, zoom=1.0, focus=None, t=0.0, chrome=True):
    """The real page, scrolled and pushed in, inside a browser frame.

    scroll is in page pixels. zoom pushes in on `focus`, a point in page space.
    Returns a mapper from page coordinates to screen coordinates, so a
    highlight can sit on the actual element rather than near it.
    """
    src = page(name)
    bar = 54 if chrome else 0
    vx, vy = 96, 96 + bar
    vw, vh = W - 192, H - 192 - bar

    sw, sh = int(vw / zoom), int(vh / zoom)
    cx = focus[0] if focus else src.width / 2
    left = int(clamp(cx - sw / 2, 0, max(0, src.width - sw)))
    top = int(clamp(scroll, 0, max(0, src.height - sh)))
    crop = src.crop((left, top, left + sw, top + sh)).resize((vw, vh), Image.BILINEAR)

    d = ImageDraw.Draw(img)
    if chrome:
        d.rectangle([vx, 96, vx + vw, 96 + bar], fill=(17, 19, 22))
        for i in range(3):
            c = vx + 26 + i * 22
            d.ellipse([c, 96 + 22, c + 10, 96 + 32], fill=(52, 56, 60))
        d.text((vx + 112, 96 + 35), "polymarct.xyz/%s" % ("" if name == "index" else name),
               font=F(20, True), fill=DIM, anchor="ls")
        d.text((vx + vw - 22, 96 + 35), "LIVE", font=F(18, True), fill=ACID, anchor="rs")
    img.paste(crop, (vx, vy))
    d.rectangle([vx, 96, vx + vw, vy + vh], outline=LINE2, width=2)

    def to_screen(px, py):
        return (vx + (px - left) * vw / sw, vy + (py - top) * vh / sh)

    return to_screen, (vx, vy, vx + vw, vy + vh)


def spot(img, box, label=None, p=1.0, boxes=None):
    """Acid corner brackets that snap onto something real on the page."""
    if p <= 0.02:
        return
    d = ImageDraw.Draw(img)
    x1, y1, x2, y2 = box
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    k = lerp(1.35, 1.0, out_expo(clamp(p * 1.6)))
    x1, x2 = cx - (cx - x1) * k, cx + (x2 - cx) * k
    y1, y2 = cy - (cy - y1) * k, cy + (y2 - cy) * k
    L = 34
    for (ax, ay, dx, dy) in ((x1, y1, 1, 1), (x2, y1, -1, 1), (x1, y2, 1, -1), (x2, y2, -1, -1)):
        d.line([ax, ay, ax + L * dx, ay], fill=ACID, width=4)
        d.line([ax, ay, ax, ay + L * dy], fill=ACID, width=4)
    if label and p > .5:
        d.text((x1, y1 - 16), label, font=F(19, True), fill=ACID, anchor="ls")
        if boxes is not None:
            boxes.append((d.textbbox((x1, y1 - 16), label, font=F(19, True), anchor="ls"), label))


def cursor(img, x, y, click=0.0):
    d = ImageDraw.Draw(img)
    if click > 0:
        r = 8 + 46 * click
        d.ellipse([x - r, y - r, x + r, y + r], outline=ACID, width=max(1, int(4 * (1 - click))))
    d.polygon([(x, y), (x, y + 24), (x + 6, y + 18), (x + 11, y + 28),
               (x + 15, y + 26), (x + 10, y + 16), (x + 17, y + 16)], fill=WHITE,
              outline=(10, 11, 12))


def text(d, s, x, y, size=40, mono=False, color=WHITE, anchor="ls", alpha=1.0, boxes=None):
    if alpha <= 0.02 or not s:
        return
    col = color if alpha >= .99 else tuple(int(c * alpha + BG[i] * (1 - alpha)) for i, c in enumerate(color))
    f = F(size, mono)
    d.text((x, y), s, font=f, fill=col, anchor=anchor)
    if boxes is not None and s.strip():
        boxes.append((d.textbbox((x, y), s, font=f, anchor=anchor), s[:24]))


def typed(s, p):
    n = int(len(s) * clamp(p))
    return s[:n]


# ---------------------------------------------------------------- effects
def split(img, amount):
    """Chromatic aberration. Sells every transition."""
    if amount < 0.4:
        return img
    r, g, b = img.split()[:3]
    o = int(amount)
    r = ImageChops.offset(r, o, 0)
    b = ImageChops.offset(b, -o, 0)
    return Image.merge("RGB", (r, g, b)).convert("RGBA")


def glitch(img, amount, seed):
    """Horizontal slices, torn and shifted."""
    if amount <= 0.01:
        return img
    rnd = random.Random(seed)
    out = img.copy()
    for _ in range(int(3 + 18 * amount)):
        y = rnd.randrange(0, H - 8)
        h = rnd.randrange(6, int(10 + 90 * amount))
        dx = rnd.randint(-int(20 + 200 * amount), int(20 + 200 * amount))
        band = img.crop((0, y, W, min(H, y + h)))
        out.paste(ImageChops.offset(band, dx, 0), (0, y))
    return out


def bloom(img, strength=0.55):
    """Let the acid glow, only the acid."""
    px = img.convert("RGB")
    mask = px.point(lambda v: 255 if v > 150 else 0)
    r, g, b = mask.split()
    hot = Image.merge("RGB", (r, g, b)).filter(ImageFilter.GaussianBlur(22))
    hot = ImageChops.multiply(hot, px)
    return Image.blend(px, ImageChops.add(px, hot.point(lambda v: int(v * strength))), 0.85).convert("RGBA")


def scanlines(img, t, strength=16):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    off = int(t * 40) % 4
    for y in range(off, H, 4):
        d.line([0, y, W, y], fill=(242, 239, 233, strength))
    img.alpha_composite(lay)
    return img


def build_vignette():
    v = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(v)
    steps = 24
    for i in range(steps):
        a = int(160 * (i / steps) ** 2.2)
        ins = int(W * 0.5 * (1 - i / steps))
        d.ellipse([-W * .30 + ins, -H * .55 + ins, W * 1.30 - ins, H * 1.55 - ins],
                  outline=(0, 0, 0, a), width=max(2, int(W * .5 / steps) + 2))
    return v.filter(ImageFilter.GaussianBlur(44))


def crt_on(img, p):
    """Power on: a hairline that opens into the picture."""
    if p >= 1:
        return img
    out = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    k = out_expo(clamp(p * 1.25))
    h = max(2, int(H * k))
    band = img.resize((W, h), Image.BILINEAR)
    out.paste(band, (0, (H - h) // 2))
    d = ImageDraw.Draw(out)
    if p < .5:
        a = int(255 * (1 - p * 2))
        d.line([0, H // 2, W, H // 2], fill=(255, 255, 255, a), width=3)
    return out


# ---------------------------------------------------------------- beats
#  t0,   t1,   page,      scroll from -> to, zoom from -> to, focus
BEATS = [
    (0.0,  4.6,  None, 0, 0, 1, 1, None),          # I am TICK
    (4.6,  8.0,  "index", 0, 210, 1.0, 1.06, None),
    (8.0,  12.4, "markets", 380, 980, 1.0, 1.0, None),
    (12.4, 16.6, "market", 120, 180, 1.0, 1.35, (700, 420)),
    (16.6, 20.8, "market", 180, 220, 1.0, 1.45, (1480, 430)),
    (20.8, 24.4, "market", 700, 1020, 1.0, 1.0, None),
    (24.4, 28.2, "verdict", 430, 560, 1.0, 1.10, None),
    (28.2, 31.4, "arc", 560, 700, 1.0, 1.12, None),
    (31.4, 34.4, "leaderboard", 540, 760, 1.0, 1.05, None),
    (34.4, 38.0, None, 0, 0, 1, 1, None),          # the lock
]


def beat_at(t):
    for b in BEATS:
        if b[0] <= t < b[1]:
            return b
    return BEATS[-1]


def mark(d, cx, cy, s, bar=0.0):
    u = s / 64.0
    x, y = cx - s / 2, cy - s / 2
    for (rx, ry, rw, rh) in [(8, 7, 9, 50), (8, 7, 20, 8), (8, 49, 20, 8),
                             (47, 19, 9, 26), (36, 19, 20, 8), (36, 37, 20, 8)]:
        d.rectangle([x + rx * u, y + ry * u, x + (rx + rw) * u, y + (ry + rh) * u], fill=WHITE)
    if bar > 0:
        half = 13 * bar
        d.rectangle([x + 29.5 * u, y + (32 - half) * u, x + 34.5 * u, y + (32 + half) * u],
                    fill=ACID)


def tick_box(x, y, s):
    w = s * 0.62
    return (x - w / 2 - 12, y - s * 0.62, x + w / 2 + 12, y + s * 0.66)


def frame(t, check=False):
    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    boxes = []
    t0, t1, name, s0, s1, z0, z1, focus = beat_at(t)
    p = clamp((t - t0) / (t1 - t0))
    fresh = t - t0                                     # seconds into this beat

    # ---- cold open ---------------------------------------------------
    if t < 4.6:
        if t < 0.6:
            d.rectangle([0, 0, W, H], fill=(0, 0, 0))
        k = clamp(inv(t, 0.5, 1.5))
        if k > 0:
            TICK.draw(img, 960, 470, lerp(120, 330, out_expo(k)), pose="idle",
                      expr="wide" if t < 2.2 else "happy", t=t)
            boxes.append((tick_box(960, 470, 330), "[TICK]"))
        d = ImageDraw.Draw(img)
        line = typed("I AM TICK.", inv(t, 1.5, 2.6))
        if line:
            text(d, line, 960, 760, 96, False, WHITE, "ms", 1.0, boxes)
            if math.sin(t * 14) > 0 and len(line) < 10:
                lw = d.textlength(line, font=F(96))
                d.rectangle([960 + lw / 2 + 8, 690, 960 + lw / 2 + 16, 762], fill=ACID)
        text(d, typed("THE SMALLEST MOVE A PRICE CAN MAKE", inv(t, 2.7, 3.6)),
             960, 820, 24, True, ACID, "ms", 1.0, boxes)
        text(d, "LET ME SHOW YOU WHAT I LIVE IN.", 960, 900, 22, True, DIM, "ms",
             clamp(inv(t, 3.7, 4.3)), boxes)

    # ---- the lock ----------------------------------------------------
    elif t >= 34.4:
        q = clamp((t - 34.4) / 3.6)
        k = in_out(clamp(q * 1.5))
        mark(d, 960, 400, 250)
        if k < .93:
            TICK.draw(img, 960, lerp(760, 400, k), lerp(230, 48, k), pose="idle",
                      expr="happy", t=t, shadow=False, tape=False)
        d = ImageDraw.Draw(img)
        mark(d, 960, 400, 250, bar=clamp(inv(k, .80, 1.0)))
        a = clamp(inv(q, .30, .60))
        text(d, "POLYMARCT", 960, 660, 112, False, WHITE, "ms", a, boxes)
        text(d, "THE FUTURE HAS A PRICE.", 960, 720, 26, True, ACID, "ms", a, boxes)
        text(d, "POLYMARCT.XYZ   //   SETTLES IN USDC ON ARC", 960, 784, 19, True, DIM, "ms",
             clamp(inv(q, .5, .8)), boxes)

    # ---- the tour ----------------------------------------------------
    else:
        scroll = lerp(s0, s1, in_out(p))
        zoom = lerp(z0, z1, in_out(clamp(p * 1.2)))
        to_screen, vb = viewport(img, name, scroll, zoom, focus, t)
        d = ImageDraw.Draw(img)

        if name == "index":
            spot(img, (to_screen(240, 300)[0], to_screen(240, 300)[1],
                       to_screen(1070, 560)[0], to_screen(1070, 560)[1]),
                 "THE PITCH", clamp(inv(p, .25, .5)), boxes)
            TICK.draw(img, 1640, 820, 210, pose="point", dir="up", expr="happy", t=t)
            boxes.append((tick_box(1640, 820, 210), "[TICK]"))
            d = ImageDraw.Draw(img)
            text(d, "THIS IS POLYMARCT.", 120, 1010, 30, True, WHITE, "ls",
                 clamp(inv(p, .1, .35)), boxes)
            text(d, "A PREDICTION MARKET ON ARC", 120, 1046, 20, True, DIM, "ls",
                 clamp(inv(p, .3, .55)), boxes)

        elif name == "markets":
            hand = TICK.draw(img, 1660, 760, 200, pose="point", dir="left", expr="focus", t=t)
            boxes.append((tick_box(1660, 760, 200), "[TICK]"))
            if hand and p > .3:
                TICK.pointer(img, hand, (1180, 640))
            d = ImageDraw.Draw(img)
            text(d, "EVERY MARKET IS A QUESTION", 120, 1010, 30, True, WHITE, "ls",
                 clamp(inv(p, .08, .3)), boxes)
            text(d, "WITH EXACTLY ONE ANSWER AND A DEADLINE", 120, 1046, 20, True, DIM, "ls",
                 clamp(inv(p, .25, .5)), boxes)
            cx = lerp(1500, 1180, in_out(clamp(inv(p, .55, .95))))
            cursor(img, cx, lerp(880, 640, in_out(clamp(inv(p, .55, .95)))),
                   clamp(inv(p, .93, 1.0)))

        elif name == "market" and t < 16.6:
            a, b = to_screen(236, 352), to_screen(648, 528)
            spot(img, (a[0], a[1], b[0], b[1]), "THE NUMBER", clamp(inv(p, .3, .55)), boxes)
            hand = TICK.draw(img, 1420, 800, 215, pose="point", dir="left", expr="focus",
                             label="67", t=t)
            boxes.append((tick_box(1420, 800, 215), "[TICK]"))
            if hand and p > .45:
                TICK.pointer(img, hand, (b[0] + 44, b[1] - 24))
            d = ImageDraw.Draw(img)
            text(d, "67% IS NOT AN OPINION", 120, 1010, 30, True, WHITE, "ls",
                 clamp(inv(p, .1, .32)), boxes)
            text(d, "IT IS WHAT PEOPLE PAID", 120, 1046, 20, True, ACID, "ls",
                 clamp(inv(p, .3, .5)), boxes)

        elif name == "market" and t < 20.8:
            a, b = to_screen(1275, 268), to_screen(1700, 322)
            spot(img, (a[0], a[1], b[0], b[1]), "TAKE A SIDE", clamp(inv(p, .2, .45)), boxes)
            pressed = p > .62
            cursor(img, lerp(1500, (a[0] + b[0]) / 2 - 120, in_out(clamp(inv(p, .25, .6)))),
                   lerp(900, (a[1] + b[1]) / 2, in_out(clamp(inv(p, .25, .6)))),
                   clamp(inv(p, .60, .74)))
            TICK.draw(img, 340, 700, 220, pose="cheer" if pressed else "press",
                      dir="right", expr="happy" if pressed else "focus", t=t)
            boxes.append((tick_box(340, 700, 220), "[TICK]"))
            d = ImageDraw.Draw(img)
            text(d, "67c BUYS A DOLLAR IF IT HAPPENS", 120, 1010, 30, True, WHITE, "ls",
                 clamp(inv(p, .08, .3)), boxes)
            text(d, "THE OTHER SIDE IS ANOTHER TRADER, NEVER US", 120, 1046, 20, True, DIM, "ls",
                 clamp(inv(p, .3, .5)), boxes)

        elif name == "market":
            TICK.draw(img, 1640, 780, 200, pose="think", expr="focus", t=t)
            boxes.append((tick_box(1640, 780, 200), "[TICK]"))
            d = ImageDraw.Draw(img)
            text(d, "IT MOVES WHEN SOMEBODY KNOWS FIRST", 120, 1010, 30, True, WHITE, "ls",
                 clamp(inv(p, .1, .35)), boxes)
            text(d, "THE CHART IS THE ARGUMENT, IN PUBLIC", 120, 1046, 20, True, DIM, "ls",
                 clamp(inv(p, .32, .55)), boxes)

        elif name == "verdict":
            TICK.draw(img, 1640, 780, 205, pose="hold", dir="left", expr="happy",
                      label="YES", t=t)
            boxes.append((tick_box(1640, 780, 205), "[TICK]"))
            d = ImageDraw.Draw(img)
            text(d, "THE SOURCE IS NAMED BEFORE ANYONE TRADES", 120, 1010, 30, True, WHITE, "ls",
                 clamp(inv(p, .08, .3)), boxes)
            text(d, "EVENT, SOURCE, VERIFICATION, RESOLUTION, SETTLEMENT", 120, 1046, 20,
                 True, ACID, "ls", clamp(inv(p, .3, .55)), boxes)

        elif name == "arc":
            TICK.draw(img, 300, 760, 205, pose="idle", expr="neutral", t=t)
            boxes.append((tick_box(300, 760, 205), "[TICK]"))
            d = ImageDraw.Draw(img)
            text(d, "USDC ON ARC. NOTHING ELSE.", 560, 1010, 30, True, WHITE, "ls",
                 clamp(inv(p, .08, .32)), boxes)
            text(d, "NO OTHER TOKEN, NO OTHER CHAIN, NO CARD, NO BRIDGE IN", 560, 1046, 20,
                 True, DIM, "ls", clamp(inv(p, .3, .55)), boxes)

        elif name == "leaderboard":
            TICK.draw(img, 1640, 780, 200, pose="cheer", expr="happy", t=t)
            boxes.append((tick_box(1640, 780, 200), "[TICK]"))
            d = ImageDraw.Draw(img)
            text(d, "BEING RIGHT IS A PUBLIC RECORD", 120, 1010, 30, True, WHITE, "ls",
                 clamp(inv(p, .08, .3)), boxes)
            text(d, "RANKED ON RISK ADJUSTED CONVICTION, NEVER ON SIZE", 120, 1046, 20,
                 True, DIM, "ls", clamp(inv(p, .3, .55)), boxes)

    # ---- treatment ---------------------------------------------------
    img = bloom(img, .45)
    cut = min(fresh, t1 - t)                            # near either edge of a beat
    heat = clamp(1 - cut / 0.34) if t > 0.6 else 0
    img = split(img, 1 + heat * 14)
    if heat > .25:
        img = glitch(img, (heat - .25) * 1.1, int(t * 1000))
    img = crt_on(img, inv(t, 0.0, 0.9))
    img = scanlines(img, t)
    img.alpha_composite(VIGNETTE)
    if t > DUR - 0.5:
        img.alpha_composite(Image.new("RGBA", (W, H), BG + (int(255 * inv(t, DUR - .5, DUR)),)))

    if check:
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, sa = boxes[i]
                b, sb = boxes[j]
                if a[0] < b[2] - 3 and a[2] - 3 > b[0] and a[1] < b[3] - 3 and a[3] - 3 > b[1]:
                    OVERLAPS.append("t=%5.2f  %s X %s" % (t, sa, sb))
    return img.convert("RGB")


# ---------------------------------------------------------------- the score
def synth(path, dur):
    rate = 44100
    n = int(rate * (dur + 1.0))
    buf = [0.0] * n

    def add(start, length, fn, gain):
        a = int(start * rate)
        for i in range(int(length * rate)):
            if a + i >= n:
                break
            buf[a + i] += fn(i / rate) * gain

    def boom(f0, f1, length):
        return lambda x: math.sin(2 * math.pi * (f0 * math.exp(math.log(max(f1, 1) / f0) * x / length)) * x) \
            * math.exp(-x * 4.2 / length)

    def blip(f):
        return lambda x: (1 if math.sin(2 * math.pi * f * x) > 0 else -1) * math.exp(-x * 26)

    def sub(f, length):
        return lambda x: math.sin(2 * math.pi * f * x) * min(1, x * 6) * min(1, (length - x) * 6)

    def noise(decay=60):
        seed = [99991]

        def nz(x):
            seed[0] = (seed[0] * 1103515245 + 12345) & 0x7FFFFFFF
            return ((seed[0] / 0x7FFFFFFF) * 2 - 1) * math.exp(-x * decay)
        return nz

    # cold open: power on, then his line
    add(0.0, 0.30, noise(26), .34)
    add(0.0, 1.60, boom(170, 34, 1.60), .55)
    add(0.0, 4.60, sub(44, 4.60), .16)
    for i in range(10):                                  # the letters typing
        add(1.55 + i * 0.105, .06, blip(900 + i * 40), .05)
    add(2.70, .50, boom(240, 60, .50), .22)
    add(3.70, .40, boom(300, 90, .40), .16)

    cuts = [b[0] for b in BEATS if b[0] > 0]
    for i, c in enumerate(cuts):
        add(c, .60, boom(160, 40, .60), .44)
        add(c, .12, noise(48), .24)
        add(c + .09, .10, blip(520 + (i % 4) * 90), .07)
        nxt = cuts[i + 1] if i + 1 < len(cuts) else dur
        add(c, min(4.0, nxt - c), sub(44, min(4.0, nxt - c)), .13)

    for k in range(52):                                  # the pulse under the tour
        add(4.8 + k * .5, .07, noise(80), .055)
    add(18.9, .20, blip(680), .13)                       # the click
    add(19.1, .24, blip(880), .11)
    add(34.45, 2.6, boom(210, 26, 2.6), .62)
    add(34.45, 2.4, sub(38, 2.4), .17)

    peak = max(1e-6, max(abs(v) for v in buf))
    k = 0.89 / peak
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v * k)) * 32767))
                               for v in buf))


# ---------------------------------------------------------------- main
def main():
    global VIGNETTE
    if not os.path.isdir(SHOTS):
        print("no captures yet, run: python tools/shots.py")
        return 1
    VIGNETTE = build_vignette()

    if "--preview" in sys.argv:
        d = os.path.join(HERE, "_preview")
        os.makedirs(d, exist_ok=True)
        for t in (1.0, 2.9, 6.2, 10.0, 14.4, 19.2, 22.6, 26.0, 29.8, 33.0, 36.4):
            frame(t, check=True).save(os.path.join(d, "t%05.1f.png" % t))
            print("  t=%.1f" % t)
        for o in OVERLAPS:
            print("  OVERLAP  " + o)
        print("%d overlaps" % len(OVERLAPS))
        return 0

    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)
    total = int(DUR * FPS)
    for i in range(total):
        t = i / FPS
        frame(t, check=(i % 5 == 0)).save(os.path.join(TMP, "f%05d.jpg" % i), quality=94)
        if i % 90 == 0:
            print("  frame %d / %d" % (i, total), flush=True)
    if OVERLAPS:
        print("  %d overlapping frames, first: %s" % (len(OVERLAPS), OVERLAPS[0]))
    else:
        print("  no overlaps in any checked frame")

    wav = os.path.join(TMP, "score.wav")
    synth(wav, DUR)
    print("  score written")

    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                    "-framerate", str(FPS), "-i", os.path.join(TMP, "f%05d.jpg"),
                    "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", OUT], check=True)
    shutil.rmtree(TMP)
    print("wrote %s (%.1f MB)" % (OUT, os.path.getsize(OUT) / 1e6))
    return 0


if __name__ == "__main__":
    sys.exit(main())
