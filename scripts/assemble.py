#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble the final single-file HTML from a template + parts.

The template (copy of assets/page-template.html, filled in by you) uses
five placeholders:

  {{CSS}}      -> assets/base.css
  {{FIGS}}     -> figure section HTML (base64 images inlined)
  {{UNITS}}    -> concatenated JS: const UNITS = [...]; const UNITS_B = [...];
  {{TOOLBOX}}  -> part 3 HTML
  {{RENDER}}   -> assets/render.js

Usage
  python assemble.py --template body.html --out final.html
  python assemble.py --template body.html --out final.html \
      --units u1.js u2.js --figs figsec.html --toolbox tb.html

Any part not passed on the CLI is left as-is if the placeholder is absent,
or raises if the placeholder exists but no part was supplied.
"""

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
ASSETS = os.path.join(SKILL, "assets")


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default=None, help="英文原题 ({{TITLE}})")
    ap.add_argument("--units", nargs="*", default=[])
    ap.add_argument("--figs", default=None)
    ap.add_argument("--toolbox", default=None)
    ap.add_argument("--css", default=os.path.join(ASSETS, "base.css"))
    ap.add_argument("--render", default=os.path.join(ASSETS, "render.js"))
    args = ap.parse_args()

    html = read(args.template)

    parts = {
        "TITLE": args.title,
        "CSS": read(args.css),
        "RENDER": read(args.render),
        "UNITS": "\n".join(read(p) for p in args.units) if args.units else None,
        "FIGS": read(args.figs) if args.figs else None,
        "TOOLBOX": read(args.toolbox) if args.toolbox else None,
    }

    for key, val in parts.items():
        token = "{{%s}}" % key
        if token not in html:
            continue
        if val is None:
            sys.exit("template has %s but no part supplied (use --%s)"
                     % (token, key.lower()))
        html = html.replace(token, val)

    left = re.findall(r"\{\{[A-Z_]+\}\}", html)
    if left:
        sys.exit("unreplaced placeholders: %s" % ", ".join(sorted(set(left))))

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)

    uris = html.count("data:image/jpeg;base64")
    print("wrote %s  %.2f MB  images=%d" % (args.out, len(html) / 1e6, uris))
    if len(html) > 6_000_000:
        print("WARNING: >6 MB. Lower figure dpi/quality or width.")


if __name__ == "__main__":
    main()
