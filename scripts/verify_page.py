#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify a generated close-reading page.

  # JS syntax + rendered DOM counts
  python verify_page.py page.html --js --dom

  # screenshot one section (desktop)
  python verify_page.py page.html --shot s4b --out shot.png

  # screenshot one section at true phone width (390px)
  python verify_page.py page.html --shot u2 --mobile --out m.png

Notes baked in from experience:
* headless Chrome enforces a ~485px minimum window width, so a direct
  --window-size=390 screenshot renders at 485 and clips. To test a real
  narrow viewport, the page is loaded inside a 390px <iframe>.
* Unit ids are u1..uN (not u01). Passing --shot u02 silently matches nothing.
* Real rendered units are matched by id="u<digits>"; the JS template literal
  '<section class="unit" id="'+u.id+'">' in the dumped script would otherwise
  inflate the count by one.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome", "chromium", "chromium-browser",
]


def find_chrome():
    for c in CHROME_CANDIDATES:
        if os.path.sep in c:
            if os.path.exists(c):
                return c
        else:
            from shutil import which
            if which(c):
                return which(c)
    sys.exit("Chrome/Chromium not found; install it or pass --chrome")


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def check_js(html):
    blocks = re.findall(r"<script>(.*?)</script>", html, re.S)
    if not blocks:
        print("no <script> blocks")
        return True
    from shutil import which
    node = which("node") or "/Users/mac/.workbuddy-ai/binaries/node/versions/22.22.2-6/bin/node"
    if not (os.path.exists(node) or which("node")):
        print("node not found; skipping JS syntax check")
        return True
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write("\n".join(blocks))
        tmp = f.name
    r = run([node, "--check", tmp])
    os.unlink(tmp)
    if r.returncode == 0:
        print("JS syntax: OK (%d block(s), %d chars)" % (len(blocks), sum(map(len, blocks))))
        return True
    print("JS syntax: FAILED\n" + r.stderr)
    return False


def check_dom(html, chrome):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        tmp = f.name
    r = run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--virtual-time-budget=8000", "--dump-dom", "file://" + tmp])
    os.unlink(tmp)
    dom = r.stdout
    units = len(set(re.findall(r'<section class="unit" id="(u\d+)"', dom)))
    cards = len(re.findall(r'<div class="card" id="c-', dom))
    navs = len(set(re.findall(r'href="#(u\d+)"', dom)))
    figs = dom.count("data:image/jpeg;base64")
    print("rendered units=%d  cards=%d  nav links=%d  images=%d" % (units, cards, navs, figs))
    ok = units > 0 and cards > 0 and navs == units
    print("DOM: %s" % ("OK" if ok else "PROBLEM (units/cards/nav mismatch)"))
    return ok


def shot(html, chrome, target, out, w, h, mobile=False):
    is_unit = bool(re.match(r"^u\d+$", target))
    if is_unit:
        css = ("<style>aside,header.hero{display:none!important}.wrap{display:block!important}"
               "main>section:not(#part2){display:none!important}"
               ".unit:not(#%s){display:none!important}#part2{display:block!important}</style>" % target)
    else:
        css = ("<style>aside,header.hero{display:none!important}.wrap{display:block!important}"
               "main>section:not(#%s){display:none!important}</style>" % target)

    page = html.replace("</head>", css + "</head>", 1)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(page)
        inner = f.name

    if mobile:
        frame = ('<!DOCTYPE html><html><head><meta charset="utf-8"><style>'
                 'html,body{margin:0;padding:0;background:#fff}'
                 'iframe{width:%dpx;height:%dpx;border:0;display:block}</style></head>'
                 '<body><iframe src="file://%s"></iframe></body></html>' % (w, h, inner))
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
            f.write(frame)
            outer = f.name
        win_w = w + 120
        win_h = h
    else:
        outer = inner
        win_w, win_h = w, h

    r = run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--force-device-scale-factor=1", "--window-size=%d,%d" % (win_w, win_h),
             "--screenshot=" + out, "--virtual-time-budget=6000", "file://" + outer])
    for p in {inner, outer}:
        try:
            os.unlink(p)
        except OSError:
            pass
    if not os.path.exists(out):
        print("screenshot failed:", r.stderr[-400:])
        return False
    print("shot -> %s  %dx%d%s  %.0f KB"
          % (out, w, h, " (mobile iframe)" if mobile else "", os.path.getsize(out) / 1024))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    ap.add_argument("--js", action="store_true")
    ap.add_argument("--dom", action="store_true")
    ap.add_argument("--shot", default=None, help="section id, e.g. s4b or u2")
    ap.add_argument("--mobile", action="store_true")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=1200)
    ap.add_argument("--out", default="shot.png")
    ap.add_argument("--chrome", default=None)
    args = ap.parse_args()

    html = open(args.page, encoding="utf-8").read()
    chrome = args.chrome or find_chrome()
    ok = True
    if args.js:
        ok &= check_js(html)
    if args.dom:
        ok &= check_dom(html, chrome)
    if args.shot:
        w = 390 if args.mobile else args.width
        ok &= shot(html, chrome, args.shot, args.out, w, args.height, args.mobile)
    if not (args.js or args.dom or args.shot):
        ap.print_help()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
