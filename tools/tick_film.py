"""The TICK film, rendered straight to MP4. No browser, no HTML, no page.

    python tools/tick_film.py            full render, 24s at 30fps
    python tools/tick_film.py --preview  a handful of frames, to check framing

Pillow draws every frame, a pure Python synth writes the score to WAV, ffmpeg
muxes the two. The only dependency outside the standard library is Pillow,
which is already here for the rest of the pipeline.
"""
import os
import sys
import math
import wave
import struct
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import tick as TICK

W, H, FPS, DUR = 1920, 1080, 30, 24.0
OUT = os.path.join(ROOT, "dist", "polymarct-05-tick-1080p.mp4")
TMP = os.path.join(HERE, "_film")
BG = (8, 9, 10)
WHITE = (242, 239, 233)
ACID = (204, 255, 0)
DIM = (138, 143, 148)
RED = (255, 77, 46)
PANEL = (13, 15, 17)
LINE2 = (58, 62, 66)

F_CACHE = {}


def F(size, mono=False):
    k = (size, mono)
    if k not in F_CACHE:
        name = "consolab.ttf" if mono else "segoeuib.ttf"
        p = os.path.join(r"C:\Windows\Fonts", name)
        F_CACHE[k] = ImageFont.truetype(p, size) if os.path.exists(p) else ImageFont.load_default()
    return F_CACHE[k]


# ---------------------------------------------------------------- easing
def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def inv(v, a, b):
    return clamp((v - a) / (b - a))


def out_expo(t):
    return 1 - pow(2, -10 * t) if t < 1 else 1


def in_out(t):
    return 4 * t * t * t if t < .5 else 1 - pow(-2 * t + 2, 3) / 2


def settle(t):
    return 1 - pow(1 - t, 3) * math.cos(t * math.pi * 1.1)


def lerp(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------- drawing
def text(d, s, x, y, size=40, mono=False, color=WHITE, anchor="ls", alpha=1.0):
    if alpha <= 0.01:
        return
    col = color if alpha >= .99 else tuple(int(c * alpha + BG[i] * (1 - alpha)) for i, c in enumerate(color))
    d.text((x, y), s, font=F(size, mono), fill=col, anchor=anchor)


def ground(img, d, t, speed=0.6, alpha=0.30):
    d.rectangle([0, 0, W, H], fill=BG)
    for i in range(12):
        x = 160 + i * 160
        d.line([x, 0, x, H], fill=(16, 18, 20))
    # the market field, drifting
    rnd = 1234567
    for i in range(90):
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        fx = (rnd % W)
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        fy = (rnd % H)
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        ln = 30 + rnd % 220
        x = (fx + t * 60 * speed * (1 + (i % 5))) % (W + 400) - 200
        v = int(28 * alpha) + (i % 3) * 6
        col = (v + 10, v + 14, v + 10) if i % 11 else (60, 76, 10)
        d.line([x, fy, x + ln, fy], fill=col)


def panel(img, x, y, w, h, hot=False):
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([x, y + 24, x + w, y + h + 24], fill=(0, 0, 0, 200))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(28)))
    d = ImageDraw.Draw(img)
    d.rectangle([x, y, x + w, y + h], fill=PANEL, outline=ACID if hot else LINE2, width=3 if hot else 2)
    return d


SER = [.44, .45, .43, .46, .45, .51, .60, .59, .62, .61, .65, .73, .72, .75, .77, .79]


def chart(d, x, y, w, h, reveal):
    n = max(2, int(round(len(SER) * reveal)))
    px = lambda i: x + w * i / (len(SER) - 1)
    py = lambda v: y + h - (v - .38) * h * 1.9
    pts = [(px(i), py(SER[i])) for i in range(n)]
    if len(pts) > 2:
        d.polygon([(x, y + h)] + pts + [(pts[-1][0], y + h)], fill=(22, 30, 8))
        d.line(pts, fill=ACID, width=5, joint="curve")
    d.line([x, y + h, x + w, y + h], fill=LINE2)
    return pts[-1]


def market_card(img, x, y, w, reveal, pct=67):
    h = int(w * 0.62)
    d = panel(img, x, y, w, h)
    text(d, "CRYPTO", x + 30, y + 52, 18, True, DIM)
    text(d, "Will BTC reach $125,000", x + 30, y + 112, 34)
    text(d, "before October 31?", x + 30, y + 156, 34)
    if reveal > 0:
        text(d, "%d%%" % pct, x + 30, y + h - 76, 84, alpha=reveal)
        d.rectangle([x + 30, y + h - 54, x + w - 30, y + h - 45], fill=(42, 45, 48))
        d.rectangle([x + 30, y + h - 54, x + 30 + (w - 60) * pct / 100, y + h - 45], fill=ACID)
        text(d, "$4.82M VOL   //   18,421 TRADERS", x + 30, y + h - 22, 16, True, DIM)
    return (x + 26, y + h - 152)


def treatment(img, t):
    """Scanlines and a vignette, so the file matches the rest of the films."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for y in range(0, H, 4):
        d.line([0, y, W, y], fill=(242, 239, 233, 16))
    img.alpha_composite(lay)
    img.alpha_composite(VIGNETTE)


def build_vignette():
    v = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(v)
    steps = 26
    for i in range(steps):
        a = int(150 * (i / steps) ** 2.2)
        inset = int(W * 0.5 * (1 - i / steps))
        d.ellipse([-W * 0.30 + inset, -H * 0.55 + inset, W * 1.30 - inset, H * 1.55 - inset],
                  outline=(0, 0, 0, a), width=max(2, int(W * 0.5 / steps) + 2))
    return v.filter(ImageFilter.GaussianBlur(40))


VIGNETTE = None


# ---------------------------------------------------------------- the cut list
def frame(t):
    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)

    if t < 3.2:                                   # he climbs out of the mark
        p = t / 3.2
        ground(img, d, t, lerp(5, .6, out_expo(clamp(p * 2))), .28)
        d = ImageDraw.Draw(img)
        draw_mark(d, 960, 350, 290, out_expo(clamp(p * 2.4)))
        if p > .42:
            k = settle(clamp(inv(p, .42, .8)))
            TICK.draw(img, 960, lerp(360, 720, k), lerp(60, 225, k),
                      pose="idle", expr="happy" if p > .7 else "wide", t=t)
            d = ImageDraw.Draw(img)
        if p > .62:
            a = clamp(inv(p, .62, .85))
            text(d, "MEET TICK", 960, 900, 56, anchor="ms", alpha=a)
            text(d, "THE SMALLEST MOVE A PRICE CAN MAKE", 960, 946, 20, True, DIM, "ms", a)

    elif t < 6.6:                                 # a question with one answer
        p = (t - 3.2) / 3.4
        ground(img, d, t, .6, .26)
        d = ImageDraw.Draw(img)
        text(d, "A question with one answer.", 150, 190, 58)
        at = market_card(img, int(lerp(-760, 150, out_expo(clamp(p * 2.2)))), 300, 800,
                         clamp(inv(p, .42, .7)))
        hand = TICK.draw(img, 1470, 600, 250, pose="point", dir="left", expr="focus", t=t)
        if p > .5 and hand:
            TICK.pointer(img, hand, (620, 430))

    elif t < 10.0:                                # and a price
        p = (t - 6.6) / 3.4
        ground(img, d, t, .6, .26)
        d = ImageDraw.Draw(img)
        text(d, "And a price.", 150, 190, 58)
        at = market_card(img, 150, 300, 800, 1)
        hand = TICK.draw(img, 1470, 600, 250, pose="point", dir="left", expr="focus",
                         label="67" if p > .3 else None, t=t)
        if hand:
            TICK.pointer(img, hand, at)
        d = ImageDraw.Draw(img)
        text(d, "67 cents", 1100, 300, 54, color=ACID, alpha=clamp(inv(p, .28, .55)))
        a = clamp(inv(p, .45, .75))
        text(d, "buys one dollar", 1100, 356, 24, True, WHITE, alpha=a)
        text(d, "if this happens", 1100, 392, 24, True, WHITE, alpha=a)

    elif t < 13.8:                                # it moves
        p = (t - 10.0) / 3.8
        ground(img, d, t, lerp(.6, 2.2, p), .28)
        d = ImageDraw.Draw(img)
        text(d, "It moves when somebody", 150, 180, 54)
        text(d, "knows something first.", 150, 236, 54, color=ACID)
        tip = chart(d, 150, 480, 1080, 360, clamp(inv(p, .08, .72)))
        hand = TICK.draw(img, min(1700, tip[0] + 260), max(330, tip[1] - 190), 210,
                         pose="point", dir="left", expr="wide", t=t)
        if hand:
            TICK.pointer(img, hand, (tip[0] + 8, tip[1] - 26))
        d = ImageDraw.Draw(img)
        if p > .76:
            text(d, "+8c IN FOUR MINUTES", 1380, 900, 26, True, ACID, "rs",
                 clamp(inv(p, .76, .95)))

    elif t < 17.2:                                # you take a side
        p = (t - 13.8) / 3.4
        ground(img, d, t, .8, .24)
        d = ImageDraw.Draw(img)
        text(d, "You take a side.", 150, 190, 58)
        pressed = p > .45
        d = panel(img, 150, 300, 700, 420, pressed)
        text(d, "TAKE A POSITION", 182, 352, 18, True, DIM)
        d.rectangle([182, 384, 502, 446], fill=ACID if pressed else (23, 26, 30))
        text(d, "TAKE YES  67c", 202, 426, 24, True, (8, 9, 10) if pressed else ACID)
        d.rectangle([518, 384, 832, 446], fill=(23, 26, 30))
        text(d, "TAKE NO  33c", 538, 426, 24, True, RED)
        for i, (k, v, col) in enumerate([("AMOUNT", "100.00 USDC", WHITE),
                                         ("SHARES", "149.25 YES", WHITE),
                                         ("PAYOUT IF CORRECT", "$149.25", ACID)]):
            yy = 500 + i * 54
            text(d, k, 182, yy, 17, True, DIM)
            text(d, v, 818, yy, 21, True, col, "rs")
        TICK.draw(img, 1120, 560, 240, pose="cheer" if pressed else "press", dir="left",
                  expr="happy" if pressed else "focus", t=t)
        d = ImageDraw.Draw(img)
        a = clamp(inv(p, .55, .8))
        text(d, "POSITION", 1360, 490, 44, alpha=a)
        text(d, "CONFIRMED", 1360, 542, 44, color=ACID, alpha=a)
        text(d, "SETTLES IN USDC ON ARC", 1360, 596, 18, True, DIM, alpha=a)

    elif t < 20.6:                                # reality decides
        p = (t - 17.2) / 3.4
        ground(img, d, t, .5, .22)
        d = ImageDraw.Draw(img)
        text(d, "Reality decides.", 150, 190, 58)
        d = panel(img, 150, 300, 900, 300, True)
        text(d, "THE VERDICT ENGINE", 182, 352, 18, True, DIM)
        for i, (k, v, col) in enumerate([("SOURCE", "COINBASE BTC-USD, HOURLY CLOSE", WHITE),
                                         ("READING", "$125,412.00", ACID),
                                         ("DISPUTE WINDOW", "CLOSED, NO CHALLENGE", WHITE)]):
            yy = 412 + i * 56
            text(d, k, 182, yy, 17, True, DIM)
            text(d, v, 1018, yy, 19, True, col, "rs")
        k = settle(clamp(inv(p, .22, .5)))
        TICK.draw(img, 1420, 540, lerp(170, 265, k), pose="hold", dir="left",
                  expr="happy", label="YES" if p > .3 else None, t=t)
        d = ImageDraw.Draw(img)
        text(d, "THE SOURCE WAS NAMED BEFORE ANYONE TRADED", 150, 800, 22, True, DIM,
             alpha=clamp(inv(p, .55, .78)))

    elif t < 22.8:                                # the market pays
        p = (t - 20.6) / 2.2
        ground(img, d, t, .6, .24)
        d = ImageDraw.Draw(img)
        text(d, "The market pays.", 150, 190, 58)
        v = 149.25 * out_expo(clamp(p * 1.8))
        text(d, "$%.2f" % v, 150, 570, 180)
        text(d, "SETTLED IN USDC ON ARC", 150, 630, 24, True, ACID)
        TICK.draw(img, 1470, 560, 265, pose="cheer", dir="left", expr="happy", t=t)

    else:                                         # the lock, back into the gap
        p = (t - 22.8) / 1.2
        ground(img, d, t, .4, .20)
        d = ImageDraw.Draw(img)
        k = in_out(clamp(p * 1.5))
        draw_mark(d, 960, 380, 240, 1)
        if k < .93:
            TICK.draw(img, 960, lerp(700, 380, k), lerp(210, 46, k),
                      pose="idle", expr="happy", t=t, shadow=False, tape=False)
        d = ImageDraw.Draw(img)
        draw_mark(d, 960, 380, 240, 1, bar=clamp(inv(k, .80, 1.0)))
        a = clamp(inv(p, .3, .6))
        text(d, "POLYMARCT", 960, 640, 110, anchor="ms", alpha=a)
        text(d, "THE FUTURE HAS A PRICE.", 960, 700, 24, True, ACID, "ms", a)
        text(d, "$PMARC // SETTLES IN USDC ON ARC", 960, 748, 18, True, DIM, "ms",
             clamp(inv(p, .5, .8)))
        if p > .9:
            f = inv(p, .9, 1.0)
            fade = Image.new("RGBA", (W, H), BG + (int(255 * f),))
            img.alpha_composite(fade)

    treatment(img, t)
    return img.convert("RGB")


def draw_mark(d, cx, cy, s, reveal, bar=0.0):
    """THE BOOK, with the gap he lives in. bar = the last price, standing in it."""
    u = s / 64.0
    x, y = cx - s / 2, cy - s / 2
    for (rx, ry, rw, rh) in [(8, 7, 9, 50), (8, 7, 20, 8), (8, 49, 20, 8),
                             (47, 19, 9, 26), (36, 19, 20, 8), (36, 37, 20, 8)]:
        h = rh * reveal
        d.rectangle([x + rx * u, y + ry * u, x + (rx + rw) * u, y + (ry + h) * u], fill=WHITE)
    if bar > 0:
        half = 13 * bar
        d.rectangle([x + 29.5 * u, y + (32 - half) * u,
                     x + 34.5 * u, y + (32 + half) * u], fill=ACID)


# ---------------------------------------------------------------- the score
def synth(path, dur):
    """A pure Python synth: sub, kicks on the cuts, blips where he moves."""
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
            * math.exp(-x * 4.5 / length)

    def blip(f, length):
        return lambda x: (1 if math.sin(2 * math.pi * f * x) > 0 else -1) * math.exp(-x * 26)

    def sub(f, length):
        return lambda x: math.sin(2 * math.pi * f * x) * min(1, x * 6) * min(1, (length - x) * 6)

    def tick_(length):
        seed = [12345]

        def nz(x):
            seed[0] = (seed[0] * 1103515245 + 12345) & 0x7FFFFFFF
            return ((seed[0] / 0x7FFFFFFF) * 2 - 1) * math.exp(-x * 60)
        return nz

    add(0, 1.3, boom(150, 34, 1.3), .55)
    add(0, 0.12, tick_(0.12), .30)
    add(0, 3.2, sub(44, 3.2), .18)
    for i, dd in enumerate((0.9, 1.2, 1.5)):
        add(dd, .14, blip(420 + i * 180, .14), .10)

    beats = [3.2, 6.6, 10.0, 13.8, 17.2, 20.6, 22.8]
    for i, b in enumerate(beats):
        add(b, .55, boom(155, 40, .55), .42)
        add(b, .10, tick_(.10), .22)
        add(b + .08, .10, blip(520, .10), .07)
        nxt = beats[i + 1] if i + 1 < len(beats) else dur
        add(b, min(3.4, nxt - b), sub(44, min(3.4, nxt - b)), .14)

    for k in range(26):
        add(3.4 + k * .5, .07, tick_(.07), .06)
    add(14.4, .18, blip(680, .18), .12)
    add(14.58, .20, blip(880, .20), .10)
    add(17.3, 1.1, boom(180, 32, 1.1), .55)
    for k in range(8):
        add(20.7 + k * .12, .10, blip(420 + k * 90, .10), .08)
    add(22.85, 2.2, boom(200, 28, 2.2), .62)
    add(22.85, 2.0, sub(38, 2.0), .16)

    peak = max(1e-6, max(abs(v) for v in buf))
    scale = 0.89 / peak
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v * scale)) * 32767)) for v in buf))


# ---------------------------------------------------------------- main
def main():
    global VIGNETTE
    VIGNETTE = build_vignette()

    if "--preview" in sys.argv:
        os.makedirs(os.path.join(ROOT, "tools", "_preview"), exist_ok=True)
        for t in (1.9, 4.6, 8.2, 11.6, 15.4, 18.6, 21.3, 23.4):
            frame(t).save(os.path.join(ROOT, "tools", "_preview", "t%05.1f.png" % t))
            print("  preview t=%.1f" % t)
        return 0

    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)

    total = int(DUR * FPS)
    for i in range(total):
        frame(i / FPS).save(os.path.join(TMP, "f%05d.jpg" % i), quality=95)
        if i % 60 == 0:
            print("  frame %d / %d" % (i, total), flush=True)

    wav = os.path.join(TMP, "score.wav")
    synth(wav, DUR)
    print("  score written")

    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                    "-framerate", str(FPS), "-i", os.path.join(TMP, "f%05d.jpg"),
                    "-i", wav,
                    "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", OUT], check=True)
    shutil.rmtree(TMP)
    print("wrote %s (%.1f MB)" % (OUT, os.path.getsize(OUT) / 1e6))
    return 0


if __name__ == "__main__":
    sys.exit(main())
