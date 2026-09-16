"""Post ready content cards. Real screenshots of the real site, with TICK.

    python tools/shots.py        photograph the site first
    python tools/tick_content.py build the cards

Every card is one finished post: a hook, a real piece of the product, TICK
reacting to it, and a line that tells you something true. Nothing here is a
thumbnail grid and nothing is a mascot standing on his own with no point to
make. Captions to post with them are written to png/Content/CAPTIONS.txt.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from PIL import Image, ImageDraw, ImageFilter
import tick as TICK
from tick_cards import Card, F, W, H, M, BG, WHITE, ACID, DIM, RED, PANEL, LINE, LINE2, mark

SHOTS = os.path.join(HERE, "_shots")
OUT = os.path.join(ROOT, "png", "Content")
CACHE = {}


def shot(page):
    if page not in CACHE:
        CACHE[page] = Image.open(os.path.join(SHOTS, page + ".png")).convert("RGB")
    return CACHE[page]


class Post(Card):
    def head(self, eyebrow):
        self.d.ellipse([M, M - 20, M + 12, M - 8], fill=ACID)
        self.tx(eyebrow, M + 26, M, 19, True, DIM)
        self.tx("POLYMARCT.XYZ", W - M, M, 19, True, DIM, anchor="rs")
        self.d.line([M, M + 22, W - M, M + 22], fill=LINE)

    def foot(self, line="THE FUTURE HAS A PRICE."):
        self.d.line([M, H - 116, W - M, H - 116], fill=LINE)
        mark(self.d, M, H - 100, 34)
        self.tx("POLYMARCT", M + 48, H - 74, 24, False, WHITE)
        self.tx(line, W - M, H - 74, 17, True, DIM, anchor="rs")

    def viewport(self, page, box, x, y, w, url, scale_note=None):
        """A real capture of the site, in a frame that says where it came from."""
        im = shot(page).crop(box)
        h = int(w * im.height / im.width)
        im = im.resize((w, h), Image.LANCZOS)
        bar = 36
        sh = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rectangle([x, y + 26, x + w, y + h + bar + 26], fill=(0, 0, 0, 210))
        self.img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(30)))
        self.img.paste(im, (x, y + bar))
        self.d = ImageDraw.Draw(self.img)
        self.d.rectangle([x, y, x + w, y + bar], fill=(17, 19, 22))
        for i in range(3):
            cx = x + 20 + i * 18
            self.d.ellipse([cx, y + 14, cx + 8, y + 22], fill=(52, 56, 60))
        self.d.text((x + 82, y + 25), url, font=F(16, True), fill=DIM, anchor="ls")
        if scale_note:
            self.d.text((x + w - 16, y + 25), scale_note, font=F(15, True), fill=(70, 74, 78),
                        anchor="rs")
        self.d.rectangle([x, y, x + w, y + h + bar], outline=LINE2, width=1)
        self.boxes.append(((x, y, x + w, y + h + bar), "[SITE %s]" % page))
        return (x, y + bar, x + w, y + h + bar)

    def spot(self, box, label=None):
        """Acid corner brackets around something real in the capture."""
        x1, y1, x2, y2 = box
        L = 26
        for (cx, cy, dx, dy) in ((x1, y1, 1, 1), (x2, y1, -1, 1), (x1, y2, 1, -1), (x2, y2, -1, -1)):
            self.d.line([cx, cy, cx + L * dx, cy], fill=ACID, width=3)
            self.d.line([cx, cy, cx, cy + L * dy], fill=ACID, width=3)
        if label:
            self.tx(label, x1, y1 - 14, 17, True, ACID)

    def save(self, name):
        os.makedirs(OUT, exist_ok=True)
        p = os.path.join(OUT, name)
        self.img.convert("RGB").quantize(colors=256, method=Image.MEDIANCUT,
                                         dither=Image.FLOYDSTEINBERG).save(p, optimize=True)
        return p


# ---------------------------------------------------------------- the cards
def c01():
    c = Post()
    c.grid()
    c.head("MEET TICK")
    c.tx("I am TICK.", M, 250, 86)
    c.tx("I live in the gap between", M, 320, 44, color=DIM)
    c.tx("the two sides of the book.", M, 372, 44, color=DIM)
    c.para("A tick is the smallest move a price can make. POLYMARCT is a prediction "
           "market on Arc: a question with one answer, a price that says how likely "
           "it is, and a named source that settles it. I will show you around.",
           M, 440, 620, 20, True, DIM)
    c.viewport("index", (200, 240, 1760, 770), 800, 210, 700, "polymarct.xyz")
    c.mascot(x=1150, y=640, s=210, pose="point", dir="up", expr="happy", t=0, blink=False)
    c.foot("$PMARC // SETTLES IN USDC ON ARC")
    return c, "01-i-am-tick.png"


def c02():
    c = Post()
    c.grid()
    c.head("WHAT THE NUMBER MEANS")
    c.tx("67% is not an opinion.", M, 250, 66)
    c.tx("It is what people paid.", M, 322, 66, color=ACID)
    c.para("Every trade moves it. If you think the crowd is wrong, the price is your "
           "offer, not somebody else's guess.", M, 382, 700, 21, True, DIM)
    box = c.viewport("market", (200, 130, 1300, 680), M, 440, 600, "polymarct.xyz/market")
    hand = c.mascot(x=1240, y=470, s=250, pose="point", dir="left", expr="focus",
                    label="67", t=0, blink=False)
    if hand:
        TICK.pointer(c.img, hand, (box[0] + 22, box[1] + 112))
    c.d = ImageDraw.Draw(c.img)
    c.tx("THE PRICE IS THE FORECAST", 1030, 700, 22, True, WHITE)
    c.para("A market at 67 cents is the crowd saying two in three. Not a slogan, "
           "a number somebody is standing behind with money.",
           1030, 740, 480, 18, True, DIM)
    c.foot("$PMARC // SETTLES IN USDC ON ARC")
    return c, "02-the-number.png"


def c03():
    c = Post()
    c.grid()
    c.head("WHAT YOU ARE BUYING")
    c.tx("67c buys a dollar", M, 250, 66)
    c.tx("if it happens.", M, 322, 66, color=ACID)
    c.para("You are not placing a bet with a house. You are buying a share that pays "
           "one dollar if the answer turns out to be yes, and nothing if it does not. "
           "The other side is another trader, never us.", M, 390, 700, 21, True, DIM)
    c.viewport("market", (1262, 165, 1712, 715), 1010, 210, 380, "polymarct.xyz/market")
    c.mascot(x=1490, y=430, s=210, pose="press", dir="left", expr="focus", t=0, blink=False)
    c.tx("COLLATERAL AND SETTLEMENT ARE USDC ON ARC. NOTHING ELSE IS ACCEPTED.",
         M, 660, 18, True, ACID)
    c.para("No ETH, no second token, no other chain, no card, no swap, no bridge in. "
           "$PMARC is not needed to trade.", M, 696, 700, 18, True, DIM)
    c.foot("MAX LOSS IS WHAT YOU COMMIT")
    return c, "03-what-you-buy.png"


def c04():
    c = Post()
    c.grid()
    c.head("THE BOARD")
    c.tx("One question. Two outcomes.", M, 244, 60)
    c.tx("Infinite information.", M, 308, 60, color=DIM)
    c.viewport("markets", (234, 620, 1690, 1240), M, 360, 900, "polymarct.xyz/markets")
    c.mascot(x=1370, y=540, s=250, pose="idle", expr="neutral", t=0, blink=False)
    c.foot("CRYPTO // MACRO // POLITICS // SPORTS // TECH // CULTURE // ARC")
    return c, "04-the-board.png"


def c05():
    c = Post()
    c.grid()
    c.head("HOW IT RESOLVES")
    c.tx("The source is named", M, 246, 62)
    c.tx("before anyone trades.", M, 312, 62, color=ACID)
    c.para("Resolution is the product. Everything upstream is just pricing. The criterion "
           "and the data source are written into the market at creation and cannot change "
           "after trading opens.", M, 372, 940, 21, True, DIM)
    c.viewport("verdict", (234, 520, 1690, 760), M, 470, 1180, "polymarct.xyz/verdict")
    c.mascot(x=1400, y=560, s=240, pose="hold", dir="left", expr="happy", label="YES",
             t=0, blink=False)
    c.tx("A DISPUTE WINDOW STANDS BETWEEN THE VERDICT AND SETTLEMENT. IT IS BONDED.",
         M, 748, 18, True, DIM)
    c.foot("THE VERDICT IS IN")
    return c, "05-reality-decides.png"


def c06():
    c = Post()
    c.grid()
    c.head("WHY ARC")
    c.tx("USDC on Arc.", M, 250, 72)
    c.tx("Nothing else.", M, 328, 72, color=ACID)
    c.para("A prediction market needs a fixed unit of account, cheap frequent price "
           "updates, and a settlement guarantee that does not move after the verdict. "
           "That is the whole reason this is built on Arc.", M, 396, 700, 21, True, DIM)
    c.viewport("arc", (234, 620, 1690, 900), M, 500, 1180, "polymarct.xyz/arc")
    c.mascot(x=1330, y=330, s=260, pose="idle", expr="neutral", t=0, blink=False)
    c.foot("ONE ASSET IN, ONE ASSET OUT")
    return c, "06-usdc-on-arc.png"


def c07():
    c = Post()
    c.grid()
    c.head("THE CONVICTION INDEX")
    c.tx("Consensus is cheap.", M, 246, 62)
    c.tx("Conviction is expensive.", M, 312, 62, color=ACID)
    c.para("Traders are ranked on risk adjusted performance across resolved markets, not "
           "on how much money they moved. A leaderboard that rewards size is a "
           "leaderboard that rewards wash trading.", M, 372, 940, 21, True, DIM)
    c.viewport("leaderboard", (234, 600, 1690, 1000), M, 460, 1000, "polymarct.xyz/leaderboard")
    c.mascot(x=1400, y=560, s=230, pose="think", expr="focus", t=0, blink=False)
    c.foot("BEING RIGHT IS A PUBLIC RECORD")
    return c, "07-public-record.png"


def c08():
    c = Post()
    c.grid()
    c.head("MAKE A MARKET")
    c.tx("If the question is real,", M, 250, 62)
    c.tx("you can publish it.", M, 316, 62, color=ACID)
    c.para("A market needs a question with exactly one answer, a deadline, a named "
           "source that can be read by anyone, and a bond from you. Vague questions "
           "are rejected by the validator, not by an opinion.", M, 380, 700, 21, True, DIM)
    c.viewport("create", (234, 500, 1690, 1040), M, 490, 690, "polymarct.xyz/create")
    c.mascot(x=1330, y=430, s=250, pose="point", dir="down", expr="focus", t=0, blink=False)
    c.foot("YOUR QUESTION, YOUR BOND, EVERYONE'S PRICE")
    return c, "08-make-a-market.png"


CAPTIONS = """POLYMARCT // CONTENT CARDS, WHAT TO SAY WITH THEM

Post one a day. Never lead with the token. Never promise a return.

01-i-am-tick.png
    I am TICK. I live in the gap between the two sides of the book.
    A tick is the smallest move a price can make.
    POLYMARCT is a prediction market on Arc. Let me show you around.

02-the-number.png
    67% is not an opinion. It is what people paid.
    Every headline gives you a take. A market gives you a number that
    somebody is standing behind with money.

03-what-you-buy.png
    You are not betting against a house.
    67c buys a share that pays $1 if the answer is yes, and nothing if it
    is not. The other side of your trade is another trader.
    Collateral and settlement are USDC on Arc. Nothing else is accepted.

04-the-board.png
    One question. Two outcomes. Infinite information.
    Crypto, macro, politics, sports, tech, culture, and Arc itself.

05-reality-decides.png
    The source is named before anyone trades.
    Criterion and data source are written into the market at creation and
    cannot change after trading opens. Then a bonded dispute window.

06-usdc-on-arc.png
    Fixed unit of account. Cheap frequent price updates. Settlement that
    does not move after the verdict.
    That is why this is on Arc, and why USDC is the only asset it takes.

07-public-record.png
    Consensus is cheap. Conviction is expensive.
    Ranked on risk adjusted performance across resolved markets, not on
    volume. A leaderboard that rewards size rewards wash trading.

08-make-a-market.png
    If the question is real, you can publish it.
    One answer, a deadline, a source anyone can read, and your bond.
    Vague questions are rejected by the validator, not by an opinion.

Rules that travel with these files
    no promised returns, no guaranteed, no risk free, no APY
    the product is the hook, the token is never the hook
    USDC on Arc is the only asset the product accepts
    every screenshot here is the real site, keep it that way
"""


def main():
    os.makedirs(OUT, exist_ok=True)
    if not os.path.isdir(SHOTS):
        print("no captures yet, run: python tools/shots.py")
        return 1
    bad = 0
    for fn in (c01, c02, c03, c04, c05, c06, c07, c08):
        c, name = fn()
        hits = c.collisions()
        if hits:
            bad += 1
            print("  OVERLAP %-26s %s" % (name, " | ".join(hits)))
        else:
            print("  clean   %s" % name)
        c.grain(6)
        c.save(name)
    open(os.path.join(OUT, "CAPTIONS.txt"), "w", encoding="utf-8").write(CAPTIONS)
    print("done, %d cards with overlaps" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
