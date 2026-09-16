"""Static audit of the Polymarct repo.

Checks the things that silently rot: dead local links, missing assets, claims
the brief forbids, rules that are supposed to appear on every page, secrets,
and repo weight. Prints findings grouped by severity and exits non-zero if
anything blocking is found.

    python tools/audit.py
"""
import os
import re
import glob
import json
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIND = {"BLOCK": [], "WARN": [], "NOTE": []}


def add(sev, area, msg):
    FIND[sev].append((area, msg))


def html_files():
    out = []
    for pat in ("*.html", "brand/*.html", "brand/motion/*.html"):
        out += sorted(glob.glob(os.path.join(ROOT, pat)))
    return out


# ---------- 1. local references resolve ----------
REF = re.compile(r'(?:href|src)="([^"#?][^"]*?)"')


def check_links():
    for f in html_files():
        base = os.path.dirname(f)
        src = open(f, encoding="utf-8").read()
        for ref in REF.findall(src):
            if ref.startswith(("http://", "https://", "mailto:", "data:", "//")):
                continue
            target = os.path.normpath(os.path.join(base, ref.split("?")[0].split("#")[0]))
            if not os.path.exists(target):
                add("BLOCK", "links", "%s -> %s (missing)" % (os.path.relpath(f, ROOT), ref))


# ---------- 2. claims the brief forbids ----------
BANNED = [
    (r"\bguaranteed?\b(?!\s+(?:to\s+lose|returns?\s+are\s+not))", "guarantee language"),
    (r"\brisk[- ]free\b", "risk free"),
    (r"\bAPY\b", "APY"),
    (r"\bpassive income\b", "passive income"),
    (r"\bto the moon\b", "moon"),
    (r"\bwill (?:moon|explode|pump)\b", "price promise"),
    (r"\bx100\b|\b100x guaranteed\b", "multiplier promise"),
]
# "settlement guarantee" is a property of the chain, not a promise about money.
# A checker that cries wolf gets ignored, which is worse than not having one.
ALLOW_CONTEXT = ["settlement guarantee", "no guaranteed", "not guaranteed", "no promised", "never guaranteed",
                 "no \"guaranteed\"", "no guarantees", "guaranteed returns, no",
                 "no apy", "fabricated apy", "fake apy", "risk free\", no", "no \"risk free\""]


def check_claims():
    for f in html_files() + glob.glob(os.path.join(ROOT, "*.md")) + glob.glob(os.path.join(ROOT, "png", "**", "*.txt"), recursive=True):
        txt = open(f, encoding="utf-8", errors="ignore").read()
        low = txt.lower()
        for pat, label in BANNED:
            for m in re.finditer(pat, txt, re.I):
                s = max(0, m.start() - 60)
                ctx = low[s:m.end() + 20]
                if any(a in ctx for a in ALLOW_CONTEXT):
                    continue
                add("BLOCK", "claims", "%s: %s -> ...%s..." %
                    (os.path.relpath(f, ROOT), label, txt[s:m.end() + 20].replace("\n", " ").strip()))


# ---------- 3. rules that must be visible ----------
def check_rules():
    pages = [f for f in html_files() if os.path.dirname(f) == ROOT]
    for f in pages:
        src = open(f, encoding="utf-8").read()
        name = os.path.basename(f)
        if 'src="assets/js/ui.js"' not in src and name != "404.html":
            add("WARN", "rules", "%s does not load ui.js, so it carries no footer disclosure" % name)
    ui = open(os.path.join(ROOT, "assets", "js", "ui.js"), encoding="utf-8").read()
    for must, label in [("USDC on Arc", "USDC only rule"),
                        ("demonstration data", "demo state disclosure"),
                        ("jurisdiction gating", "eligibility disclosure")]:
        if must.lower() not in ui.lower():
            add("BLOCK", "rules", "footer is missing: %s" % label)


# ---------- 4. secrets ----------
SECRET = [
    (r"(?i)\b(?:api[_-]?key|secret|private[_-]?key|passwd|password)\s*[:=]\s*['\"][^'\"]{12,}", "hardcoded credential"),
    (r"0x[a-fA-F0-9]{64}", "possible private key"),
    (r"(?i)AKIA[0-9A-Z]{16}", "aws key"),
]


def check_secrets():
    for f in glob.glob(os.path.join(ROOT, "**", "*.*"), recursive=True):
        if any(p in f for p in (".git", "png" + os.sep, "dist" + os.sep)):
            continue
        if os.path.splitext(f)[1].lower() not in (".js", ".py", ".html", ".json", ".md", ".txt", ".css"):
            continue
        try:
            txt = open(f, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for pat, label in SECRET:
            if re.search(pat, txt):
                add("BLOCK", "secrets", "%s: %s" % (os.path.relpath(f, ROOT), label))


# ---------- 5. data integrity ----------
def check_data():
    src = open(os.path.join(ROOT, "assets", "js", "data.js"), encoding="utf-8").read()
    ids = re.findall(r'\{\s*id:"([^"]+)"', src)
    if len(ids) != len(set(ids)):
        dupes = [i for i in set(ids) if ids.count(i) > 1]
        add("BLOCK", "data", "duplicate market ids: %s" % ", ".join(dupes))
    add("NOTE", "data", "%d markets defined" % len(ids))
    for field in ("crit:", "src:", "ends:"):
        n = src.count(field)
        if n < len(ids):
            add("BLOCK", "data", "%d of %d markets missing %s" % (len(ids) - n, len(ids), field.strip(":")))
    for m in re.finditer(r'ends:"([^"]+)"', src):
        if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", m.group(1)):
            add("WARN", "data", "odd resolution timestamp: %s" % m.group(1))


# ---------- 6. weight ----------
def check_weight():
    total = 0
    big = []
    for f in glob.glob(os.path.join(ROOT, "**", "*"), recursive=True):
        if os.path.isfile(f) and ".git" not in f:
            sz = os.path.getsize(f)
            total += sz
            if sz > 20 * 1024 * 1024:
                big.append((os.path.relpath(f, ROOT), sz))
    add("NOTE", "weight", "repo payload %.0f MB" % (total / 1e6))
    for f, sz in big:
        add("WARN", "weight", "%s is %.0f MB, close to the 100 MB file limit" % (f, sz / 1e6))
    if total > 400e6:
        add("WARN", "weight", "repo is heavy for GitHub Pages, consider moving media out")


# ---------- 7. accessibility basics ----------
def check_a11y():
    for f in html_files():
        src = open(f, encoding="utf-8").read()
        rel = os.path.relpath(f, ROOT)
        if "<html" in src and 'lang="' not in src:
            add("WARN", "a11y", "%s has no lang attribute" % rel)
        for img in re.finditer(r"<img\b[^>]*>", src):
            if "alt=" not in img.group(0):
                add("WARN", "a11y", "%s has an img without alt" % rel)
        if "<title>" not in src:
            add("BLOCK", "a11y", "%s has no title" % rel)


def main():
    check_links()
    check_claims()
    check_rules()
    check_secrets()
    check_data()
    check_weight()
    check_a11y()

    for sev in ("BLOCK", "WARN", "NOTE"):
        items = FIND[sev]
        print("\n%s  (%d)" % (sev, len(items)))
        print("-" * 60)
        for area, msg in items:
            print("  [%s] %s" % (area, msg))
    print()
    return 1 if FIND["BLOCK"] else 0


if __name__ == "__main__":
    sys.exit(main())
