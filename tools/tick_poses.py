"""One image per pose. One pose per image. Nothing tiled.

    python tools/tick_poses.py

Writes two files for every pose into png/Tick/:

    pose-NN-<name>.png    1200x1200, full frame, on the brand black
    cutout-<name>.png     the same pose with no background, to drop on anything

No grids, no sheets, no thumbnails. If you want to see a pose, you open that
pose's file and it fills the screen.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from PIL import Image, ImageDraw, ImageFont
import tick as TICK

S = 1200
BG = (8, 9, 10)
WHITE = (242, 239, 233)
ACID = (204, 255, 0)
DIM = (138, 143, 148)
OUT = os.path.join(ROOT, "png", "Tick")

FONTS = {}


def F(size, mono=True):
    k = (size, mono)
    if k not in FONTS:
        p = os.path.join(r"C:\Windows\Fonts", "consolab.ttf" if mono else "segoeuib.ttf")
        FONTS[k] = ImageFont.truetype(p, size) if os.path.exists(p) else ImageFont.load_default()
    return FONTS[k]


# name, caption, draw arguments
POSES = [
    ("idle",     "Standing by",              dict(pose="idle", expr="neutral")),
    ("point",    "Pointing at a number",     dict(pose="point", dir="left", expr="focus")),
    ("point-up", "Pointing at a move up",    dict(pose="point", dir="up", expr="wide")),
    ("think",    "Working it out",           dict(pose="think", expr="focus", tick="down")),
    ("cheer",    "The position paid",        dict(pose="cheer", expr="happy")),
    ("confused", "The oracle is confused",   dict(pose="confused", expr="confused", tick="down")),
    ("hold",     "Holding a verdict",        dict(pose="hold", expr="happy", label="YES")),
    ("press",    "Taking the position",      dict(pose="press", expr="focus")),
    ("price",    "Carrying a price",         dict(pose="idle", expr="neutral", label="67")),
    ("split",    "A market that cannot decide", dict(pose="think", expr="wide", label="51/49")),
]


def plate(name, caption, kw):
    img = Image.new("RGBA", (S, S), BG + (255,))
    d = ImageDraw.Draw(img)
    for i in range(1, 12):
        x = S * i / 12
        d.line([x, 0, x, S], fill=(16, 18, 20))
    d.line([90, S - 118, S - 90, S - 118], fill=(34, 37, 40))

    TICK.draw(img, S / 2, S / 2 - 30, 630, t=0.0, blink=False, **kw)

    d = ImageDraw.Draw(img)
    d.ellipse([90, S - 92, 102, S - 80], fill=ACID)
    d.text((118, S - 78), name.upper().replace("-", " "), font=F(30), fill=WHITE, anchor="ls")
    d.text((S - 90, S - 78), caption.upper(), font=F(22), fill=DIM, anchor="rs")
    return img.convert("RGB")


def cutout(kw):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    TICK.draw(img, S / 2, S / 2, 780, t=0.0, blink=False, shadow=False, **kw)
    return img.crop(img.getbbox())


def main():
    os.makedirs(OUT, exist_ok=True)
    sheet = os.path.join(OUT, "sheet.png")
    if os.path.exists(sheet):
        os.remove(sheet)
        print("removed the old tiled sheet")

    for i, (name, caption, kw) in enumerate(POSES, 1):
        p = os.path.join(OUT, "pose-%02d-%s.png" % (i, name))
        plate(name, caption, kw).quantize(colors=256, method=Image.MEDIANCUT,
                                          dither=Image.FLOYDSTEINBERG).save(p, optimize=True)
        c = os.path.join(OUT, "cutout-%s.png" % name)
        cutout(kw).save(c, optimize=True)
        print("  %-28s %-24s" % (os.path.basename(p), os.path.basename(c)))

    print("done, %d poses, one image each" % len(POSES))


if __name__ == "__main__":
    main()
