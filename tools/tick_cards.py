"""TICK content cards, rendered straight to PNG. No browser, no page.

    python tools/tick_cards.py

Every string is measured and its box recorded, TICK included, so an overlap is
a build failure rather than something spotted after posting.
"""
import os
import sys
import math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import tick as TICK

W, H, M = 1600, 900, 88
BG = (8, 9, 10)
WHITE = (242, 239, 233)
ACID = (204, 255, 0)
DIM = (138, 143, 148)
RED = (255, 77, 46)
PANEL = (13, 15, 17)
LINE = (38, 41, 44)
LINE2 = (62, 66, 70)

FONTS = {}


def F(size, mono=False, weight="bold"):
    key = (size, mono, weight)
    if key in FONTS:
        return FONTS[key]
    if mono:
        names = ["consolab.ttf" if weight == "bold" else "consola.ttf"]
    else:
        names = ["segoeuib.ttf", "arialbd.ttf"] if weight == "bold" else ["segoeui.ttf", "arial.ttf"]
    for n in names:
        p = os.path.join(r"C:\Windows\Fonts", n)
        if os.path.exists(p):
            FONTS[key] = ImageFont.truetype(p, size)
            return FONTS[key]
    FONTS[key] = ImageFont.load_default()
    return FONTS[key]


class Card:
    def __init__(self):
        self.img = Image.new("RGBA", (W, H), BG + (255,))
        self.d = ImageDraw.Draw(self.img)
        self.boxes = []

    def tx(self, s, x, y, size=24, mono=False, color=WHITE, anchor="ls", weight="bold"):
        f = F(size, mono, weight)
        if s.strip():
            box = self.d.textbbox((x, y), s, font=f, anchor=anchor)
            self.boxes.append((box, s[:26]))
        self.d.text((x, y), s, font=f, fill=color, anchor=anchor)
        return self.d.textlength(s, font=f)

    def wrap(self, s, maxw, size, mono=False):
        f = F(size, mono)
        out, line = [], ""
        for word in s.split(" "):
            t = (line + " " + word).strip()
            if self.d.textlength(t, font=f) > maxw and line:
                out.append(line)
                line = word
            else:
                line = t
        if line:
            out.append(line)
        return out

    def para(self, s, x, y, maxw, size=20, mono=True, color=DIM, lh=None):
        lh = lh or int(size * 1.5)
        for i, l in enumerate(self.wrap(s, maxw, size, mono)):
            self.tx(l, x, y + i * lh, size, mono, color)
        return y

    def mascot(self, **kw):
        s = kw.get("s", 200)
        x, y = kw["x"], kw["y"]
        w = s * 0.62
        self.boxes.append(((x - w / 2 - 10, y - s * 0.62, x + w / 2 + 10, y + s * 0.66), "[TICK]"))
        return TICK.draw(self.img, **kw)

    def grid(self):
        for i in range(13):
            x = M + (W - M * 2) * i / 12
            self.d.line([x, M, x, H - M], fill=(17, 19, 21))

    def head(self, eyebrow, n):
        self.d.ellipse([M, M - 20, M + 12, M - 8], fill=ACID)
        self.tx(eyebrow, M + 26, M, 19, True, DIM)
        self.tx("%d / 4" % n, W - M, M, 19, True, DIM, anchor="rs")
        self.d.line([M, M + 22, W - M, M + 22], fill=LINE)

    def foot(self):
        self.d.line([M, H - M - 52, W - M, H - M - 52], fill=LINE)
        mark(self.d, M, H - M - 38, 36)
        self.tx("POLYMARCT", M + 50, H - M - 10, 26, False, WHITE)
        self.tx("$PMARC // ON ARC", W - M, H - M - 10, 17, True, DIM, anchor="rs")

    def panel(self, x, y, w, h, hot=False):
        sh = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rectangle([x, y + 22, x + w, y + h + 22], fill=(0, 0, 0, 190))
        self.img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(26)))
        self.d = ImageDraw.Draw(self.img)
        self.d.rectangle([x, y, x + w, y + h], fill=PANEL,
                         outline=ACID if hot else LINE2, width=2 if hot else 1)

    def collisions(self):
        hits = []
        for i in range(len(self.boxes)):
            for j in range(i + 1, len(self.boxes)):
                a, sa = self.boxes[i]
                b, sb = self.boxes[j]
                if a[0] < b[2] - 2 and a[2] - 2 > b[0] and a[1] < b[3] - 2 and a[3] - 2 > b[1]:
                    hits.append("%s X %s" % (sa, sb))
        return hits

    def grain(self, amt=9):
        import random
        px = self.img.load()
        rnd = random.Random(4)
        for yy in range(0, H, 2):
            for xx in range(0, W, 2):
                r, g, b, a = px[xx, yy]
                v = rnd.randint(-amt, amt)
                px[xx, yy] = (max(0, min(255, r + v)), max(0, min(255, g + v)),
                              max(0, min(255, b + v)), a)

    def save(self, name):
        out = os.path.join(ROOT, "png", "Tick", name)
        self.img.convert("RGB").quantize(colors=256, method=Image.MEDIANCUT,
                                         dither=Image.FLOYDSTEINBERG).save(out, optimize=True)
        return out


def mark(d, x, y, s):
    """THE BOOK, small, for the footer."""
    u = s / 64.0
    for (rx, ry, rw, rh) in [(8, 7, 9, 50), (8, 7, 20, 8), (8, 49, 20, 8),
                             (47, 19, 9, 26), (36, 19, 20, 8), (36, 37, 20, 8)]:
        d.rectangle([x + rx * u, y + ry * u, x + (rx + rw) * u, y + (ry + rh) * u], fill=WHITE)
    d.rectangle([x + 29 * u, y + 26 * u, x + 35 * u, y + 38 * u], fill=ACID)


def market_card(c, x, y, w, question, pct, hot=True):
    h = int(w * 0.66)
    c.panel(x, y, w, h, hot)
    c.tx("CRYPTO", x + 26, y + 46, 16, True, DIM)
    for i, l in enumerate(c.wrap(question, w - 52, 26, False)[:2]):
        c.tx(l, x + 26, y + 96 + i * 34, 26, False, WHITE)
    s = "%d%%" % pct
    wpx = c.tx(s, x + 26, y + h - 72, 72, False, WHITE)
    c.tx("YES", x + 26 + wpx + 18, y + h - 72, 20, True, DIM)
    c.d.rectangle([x + 26, y + h - 52, x + w - 26, y + h - 44], fill=(42, 45, 48))
    c.d.rectangle([x + 26, y + h - 52, x + 26 + (w - 52) * pct / 100, y + h - 44], fill=ACID)
    c.tx("$4.82M VOL   //   18,421 TRADERS", x + 26, y + h - 20, 15, True, DIM)
    return (x + 26 + wpx * 0.5, y + h - 96)


# ------------------------------------------------------------------ cards
def card1():
    c = Card(); c.grid(); c.head("TICK EXPLAINS", 1)
    c.tx("That number is the odds.", M, 190, 58, False, WHITE)
    at = market_card(c, M, 280, 720, "Will BTC reach $125,000 before October 31?", 67)
    hand = c.mascot(x=1300, y=580, s=250, pose="point", dir="left", expr="focus", t=0, blink=False)
    TICK.pointer(c.img, (hand[0], hand[1]), at)
    c.d = ImageDraw.Draw(c.img)
    c.tx("67 cents", 1060, 250, 44, False, ACID)
    c.para("is what the market charges to take YES. It is not a fee and not a guess: it is "
           "the price of a share that pays one dollar if this happens.", 1060, 296, W - M - 1060, 20)
    c.foot(); return c, "01-what-the-number-means.png"


def card2():
    c = Card(); c.grid(); c.head("TICK EXPLAINS", 2)
    c.tx("When it moves, somebody", M, 182, 54, False, WHITE)
    c.tx("knew something first.", M, 238, 54, False, ACID)
    ax, aw, ay, ah = M, 900, 640, 300
    ser = [.44, .45, .43, .46, .45, .51, .60, .59, .62, .61, .65, .73, .72, .75, .77]
    px = lambda i: ax + aw * i / (len(ser) - 1)
    py = lambda v: ay - (v - .38) * ah * 2.0
    poly = [(px(i), py(v)) for i, v in enumerate(ser)]
    c.d.polygon([(ax, ay)] + poly + [(px(len(ser) - 1), ay)], fill=(24, 32, 10))
    c.d.line(poly, fill=ACID, width=4, joint="curve")
    c.d.line([ax, ay, ax + aw, ay], fill=LINE2)
    j = 6
    c.d.ellipse([px(j) - 9, py(ser[j]) - 9, px(j) + 9, py(ser[j]) + 9], fill=ACID)
    hand = c.mascot(x=1330, y=610, s=240, pose="point", dir="left", expr="wide", t=0.4, blink=False)
    TICK.pointer(c.img, (hand[0], hand[1]), (px(j), py(ser[j]) - 16))
    c.d = ImageDraw.Draw(c.img)
    c.tx("+8 cents in four minutes", 1160, 300, 26, False, WHITE)
    c.para("Volume ran four times normal and one fill took the offer. The price did not "
           "drift, it was moved.", 1160, 340, W - M - 1160, 19)
    c.tx("A price is the only opinion that costs money to hold.", M, 780, 22, True, DIM)
    c.foot(); return c, "02-why-it-moves.png"


def card3():
    c = Card(); c.grid(); c.head("TICK EXPLAINS", 3)
    c.tx("You are buying a dollar,", M, 182, 54, False, WHITE)
    c.tx("on condition.", M, 238, 54, False, WHITE)
    x, y, w, h = M, 320, 620, 380
    c.panel(x, y, w, h)
    c.tx("TAKE A POSITION", x + 26, y + 44, 16, True, DIM)
    c.d.rectangle([x + 26, y + 70, x + 26 + (w - 52) / 2 - 4, y + 124], fill=ACID)
    c.tx("TAKE YES  67c", x + 40, y + 104, 22, True, (8, 9, 10))
    c.d.rectangle([x + 26 + (w - 52) / 2 + 4, y + 70, x + w - 26, y + 124], fill=(23, 26, 30))
    c.tx("TAKE NO  33c", x + 40 + (w - 52) / 2 + 4, y + 104, 22, True, RED)
    rows = [("AMOUNT", "100.00 USDC", WHITE), ("SHARES", "149.25 YES", WHITE),
            ("PAYOUT IF CORRECT", "$149.25", ACID), ("MAX LOSS", "$100.00", RED)]
    for i, (k, v, col) in enumerate(rows):
        yy = y + 170 + i * 46
        c.tx(k, x + 26, yy, 16, True, DIM)
        c.tx(v, x + w - 26, yy, 20, True, col, anchor="rs")
        c.d.line([x + 26, yy + 14, x + w - 26, yy + 14], fill=LINE)
    hand = c.mascot(x=900, y=520, s=230, pose="point", dir="left", expr="focus", t=0.9, blink=False)
    TICK.pointer(c.img, (hand[0], hand[1]), (x + w - 120, y + 170 + 2 * 46 - 8))
    c.d = ImageDraw.Draw(c.img)
    t0 = 1080
    c.tx("$100 buys 149.25 shares", t0, 330, 28, False, WHITE)
    c.para("Each share pays exactly one dollar if the answer is yes, and nothing if it is no. "
           "That is the whole instrument. There is no leverage hiding in it.",
           t0, 372, W - M - t0, 19)
    c.tx("SETTLES IN USDC ON ARC", t0, 560, 19, True, ACID)
    c.tx("NO OTHER ASSET, NO OTHER CHAIN", t0, 592, 17, True, DIM)
    c.foot(); return c, "03-what-you-are-buying.png"


def card4():
    c = Card(); c.grid(); c.head("TICK EXPLAINS", 4)
    c.tx("We do not decide", M, 182, 54, False, WHITE)
    c.tx("who was right.", M, 238, 54, False, WHITE)
    x, y, w, h = M, 330, 700, 300
    c.panel(x, y, w, h, hot=True)
    c.tx("THE VERDICT ENGINE", x + 26, y + 44, 16, True, DIM)
    c.tx("RESOLVED", x + w - 26, y + 44, 16, True, ACID, anchor="rs")
    for i, (k, v, col) in enumerate([
            ("SOURCE", "COINBASE BTC-USD, HOURLY CLOSE", WHITE),
            ("READING", "$125,412.00", ACID),
            ("DISPUTE WINDOW", "24H, CLOSED, NO CHALLENGE", WHITE),
            ("SETTLEMENT", "USDC ON ARC", WHITE)]):
        yy = y + 110 + i * 50
        c.tx(k, x + 26, yy, 16, True, DIM)
        c.tx(v, x + w - 26, yy, 18, True, col, anchor="rs")
        c.d.line([x + 26, yy + 16, x + w - 26, yy + 16], fill=LINE)
    c.mascot(x=980, y=520, s=240, pose="hold", dir="right", expr="happy", label="YES", t=0, blink=False)
    t0 = 1180
    c.tx("The source was named", t0, 350, 26, False, WHITE)
    c.tx("before anyone traded.", t0, 384, 26, False, ACID)
    c.para("Criteria, source and deadline are fixed and hashed at creation. The question "
           "cannot change after trading opens, and the reading that produced the verdict "
           "is published with it.", t0, 432, W - M - t0, 18)
    c.tx("A wrong verdict is worse than no verdict, so an unanswerable market voids at cost.",
         M, 780, 20, True, DIM)
    c.foot(); return c, "04-reality-decides.png"


def main():
    os.makedirs(os.path.join(ROOT, "png", "Tick"), exist_ok=True)
    bad = 0
    for fn in (card1, card2, card3, card4):
        c, name = fn()
        hits = c.collisions()
        if hits:
            bad += 1
            print("  OVERLAP %s: %s" % (name, " | ".join(hits)))
        else:
            print("  clean   %s" % name)
        c.grain()
        c.save(name)
    print("done, %d cards with overlaps" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
