"""Build the PNG deliverable tree.

Everything anyone needs to use lands in png/ as flat PNG files in numbered
folders, with a contact sheet per folder so the whole set can be browsed in an
image viewer. No page to open, no renderer to run.

    python tools/build_png.py

Two kinds of folder live here:

  DERIVED   rebuilt from elsewhere in the repo every run, safe to wipe
  AUTHORED  the cards themselves live here and nowhere else, never wiped

That distinction matters. An earlier version of this script wiped the whole
tree and refilled it from a folder that had since been deleted, which emptied
the set. Only derived folders are cleared now.
"""
import os
import shutil
import subprocess
import glob
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PNG = os.path.join(ROOT, "png")

DERIVED = {
    "01-logo":           "The mark, lockups and wordmarks",
    "02-icons":          "Favicons and app icons",
    "05-link-preview":   "The card a shared link shows",
    "06-film-stills":    "Frames pulled from the four films",
    "00-contact-sheets": "One image per folder, everything at a glance",
}
AUTHORED = {
    "03-social":  "Signal, hook, explainer and stat cards for posting",
    "04-profile": "X header and avatar",
    "Twitter":    "Ten explainer cards, one layout each",
    "Tick":       "The mascot: character sheet and the cards he explains",
}
ORDER = ["00-contact-sheets", "01-logo", "02-icons", "03-social", "04-profile",
         "05-link-preview", "06-film-stills", "Twitter", "Tick"]
NOTES = dict(DERIVED, **AUTHORED)

BLACK = (8, 9, 10)
WHITE = (242, 239, 233)
ACID = (204, 255, 0)
DIM = (138, 143, 148)


def font(size, mono=False):
    names = (["consola.ttf", "cour.ttf"] if mono else ["segoeuib.ttf", "arialbd.ttf", "arial.ttf"])
    for n in names:
        p = os.path.join(r"C:\Windows\Fonts", n)
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                pass
    return ImageFont.load_default()


def prepare():
    for name in DERIVED:
        d = os.path.join(PNG, name)
        if os.path.isdir(d):
            for f in glob.glob(os.path.join(d, "*.png")):
                os.remove(f)
        else:
            os.makedirs(d, exist_ok=True)
    for name in AUTHORED:
        os.makedirs(os.path.join(PNG, name), exist_ok=True)


def copy(src_glob, dest):
    n = 0
    for f in sorted(glob.glob(src_glob)):
        shutil.copy2(f, os.path.join(PNG, dest, os.path.basename(f)))
        n += 1
    return n


def stills():
    """Pull frames from each film so the films are postable as images too."""
    films = [
        ("polymarct-trailer-1080p.mp4", "trailer", [0.2, 2.0, 5.0, 9.8, 13.6, 17.0, 21.0, 23.0, 27.8]),
        ("polymarct-01-ident-1080p.mp4", "ident", [2.3, 4.4, 6.5, 9.0, 11.5, 14.2]),
        ("polymarct-02-flow-1080p.mp4", "flow", [2.6, 7.5, 9.6, 13.0, 17.0, 20.5, 24.5]),
        ("polymarct-03-network-1080p.mp4", "network", [3.0, 8.4, 11.0, 13.5, 17.5, 22.5]),
        ("polymarct-05-tick-1080p.mp4", "tick", [1.9, 4.6, 8.2, 11.6, 15.4, 18.6, 21.3, 23.4]),
    ]
    out = os.path.join(PNG, "06-film-stills")
    n = 0
    for fn, tag, times in films:
        src = os.path.join(ROOT, "dist", fn)
        if not os.path.exists(src):
            continue
        for t in times:
            dst = os.path.join(out, "%s-%05.1fs.png" % (tag, t))
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", src,
                            "-frames:v", "1", dst], check=False)
            if os.path.exists(dst):
                im = Image.open(dst).convert("RGB")
                im.quantize(colors=256, method=Image.MEDIANCUT,
                            dither=Image.FLOYDSTEINBERG).save(dst, optimize=True)
                n += 1
    return n


def contact_sheet(folder, title, cols=4, cell=520):
    files = sorted(glob.glob(os.path.join(PNG, folder, "*.png")))
    if not files:
        return None
    pad, head, label = 24, 150, 34
    rows = (len(files) + cols - 1) // cols
    w = pad + cols * (cell + pad)
    h = head + rows * (cell + label + pad) + pad
    sheet = Image.new("RGB", (w, h), BLACK)
    d = ImageDraw.Draw(sheet)
    d.text((pad, 44), "POLYMARCT", font=font(46), fill=WHITE)
    d.text((pad + 300, 58), title.upper(), font=font(20, True), fill=DIM)
    d.text((pad, 104), "%d FILES  //  %s" % (len(files), folder), font=font(18, True), fill=ACID)
    d.line([(pad, head - 18), (w - pad, head - 18)], fill=(40, 43, 46))

    for i, f in enumerate(files):
        im = Image.open(f).convert("RGBA")
        im.thumbnail((cell, cell), Image.LANCZOS)
        x = pad + (i % cols) * (cell + pad)
        y = head + (i // cols) * (cell + label + pad)
        tile = Image.new("RGB", (cell, cell), (18, 20, 23))
        td = ImageDraw.Draw(tile)
        for cx in range(0, cell, 24):
            for cy in range(0, cell, 24):
                if (cx // 24 + cy // 24) % 2 == 0:
                    td.rectangle([cx, cy, cx + 23, cy + 23], fill=(24, 27, 30))
        tile.paste(im, ((cell - im.width) // 2, (cell - im.height) // 2), im)
        sheet.paste(tile, (x, y))
        d.rectangle([x, y, x + cell - 1, y + cell - 1], outline=(46, 49, 52))
        name = os.path.basename(f)[:-4]
        if len(name) > 34:
            name = name[:33] + "\u2026"
        d.text((x, y + cell + 9), name, font=font(15, True), fill=DIM)

    out = os.path.join(PNG, "00-contact-sheets", folder + ".png")
    sheet.convert("RGB").quantize(colors=256, method=Image.MEDIANCUT,
                                  dither=Image.FLOYDSTEINBERG).save(out, optimize=True)
    return out


def index_txt(counts):
    lines = [
        "POLYMARCT // PNG DELIVERABLES",
        "",
        "Everything here is a PNG. Open the folder, use the file.",
        "The contact sheets in 00 show every image in a folder at a glance.",
        "",
    ]
    for name in ORDER:
        lines.append("%-20s %4d files   %s" % (name, counts.get(name, 0), NOTES.get(name, "")))
    lines += [
        "",
        "Sizes",
        "  logo            16 to 1024 px square, plus lockups to 2400 wide",
        "  icons           16 / 32 / 48 / 180 / 192 / 512",
        "  social          1600x900 for the timeline, 1080x1350 for feed footprint",
        "  Twitter         1600x900, ten layouts, checked for text collisions",
        "  Tick            1600x900 cards, plus the character sheet at 1800x1150",
        "  profile         header 1500x500, avatar 400x400",
        "  link preview    1200x630",
        "  film stills     1920x1080",
        "",
        "Rebuilding",
        "  python tools/build_png.py",
        "  01, 02, 05, 06 and the contact sheets are rebuilt from the repo.",
        "  03, 04 and Twitter are authored in place and left alone.",
        "",
        "Rules that travel with these files",
        "  no promised returns, no guaranteed, no risk free, no APY",
        "  never lead with the token, the product is the hook",
        "  USDC on Arc is the only asset the product accepts",
    ]
    open(os.path.join(PNG, "INDEX.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")


def main():
    prepare()
    counts = {}
    counts["01-logo"] = copy(os.path.join(ROOT, "brand", "logo", "png", "*.png"), "01-logo")
    counts["02-icons"] = copy(os.path.join(ROOT, "assets", "icons", "*.png"), "02-icons")
    counts["05-link-preview"] = copy(os.path.join(ROOT, "assets", "og-image.png"), "05-link-preview")
    counts["06-film-stills"] = stills()
    for name in AUTHORED:
        counts[name] = len(glob.glob(os.path.join(PNG, name, "*.png")))

    sheets = 0
    for name in ORDER:
        if name.startswith("00"):
            continue
        cols = 3 if name in ("03-social", "06-film-stills", "04-profile", "05-link-preview", "Twitter", "Tick") else 4
        if contact_sheet(name, NOTES[name], cols=cols):
            sheets += 1
    counts["00-contact-sheets"] = sheets

    index_txt(counts)
    for name in ORDER:
        print("%-20s %d" % (name, counts.get(name, 0)))
    print("total %d PNG files in %s" % (sum(counts.values()), PNG))


if __name__ == "__main__":
    main()
