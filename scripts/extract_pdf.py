#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract text and crop figures from an academic PDF.

Two modes:

  # 1) Dump text + candidate figure regions (do this first)
  python extract_pdf.py paper.pdf --work ./work --detect

  # 2) Crop exact boxes once you have chosen them (see detect output)
  python extract_pdf.py paper.pdf --work ./work --crop crops.json

crops.json format (1-based page number, PDF points):
  {"1": [2, 54, 58, 540, 458],
   "2": [4, 36, 58, 558, 376]}
  -> {"fig number": [page, x0, y0, x1, y1]}

Outputs
  --detect : work/text.txt, work/pageNN.png, work/candidates.txt
  --crop   : work/fig1.jpg ... work/figN.jpg  (+ work/figmeta.json)

Why two modes: automatic bbox detection is unreliable for multi-panel
figures (it returns one bbox per embedded raster, so a 6-panel figure
yields 6 boxes). Detect gives you the page renders + raw bboxes; you
pick one box per figure and crop precisely.
"""

import argparse
import base64
import io
import json
import os
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("PyMuPDF missing. Install into the managed venv:\n"
             "  /Users/mac/.workbuddy-ai/binaries/python/envs/default/bin/pip install pymupdf pillow")


def dump_text(doc, work):
    out = []
    for i, page in enumerate(doc, 1):
        out.append("\n===== PAGE %d =====\n" % i)
        out.append(page.get_text("text"))
    path = os.path.join(work, "text.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(out))
    return path


def detect(doc, work, dpi=110):
    """Render every page and list embedded-image bboxes.

    Avoids page.get_text('dict') and page.search_for(), which can segfault
    on some malformed PDFs. get_images + get_image_bbox is stable.
    """
    lines = []
    for i, page in enumerate(doc, 1):
        pix = page.get_pixmap(dpi=dpi)
        pix.save(os.path.join(work, "page%02d.png" % i))
        lines.append("PAGE %d  size=%.0fx%.0f pt" % (i, page.rect.width, page.rect.height))
        try:
            for img in page.get_images(full=True):
                xref = img[0]
                try:
                    bb = page.get_image_bbox(img)
                except Exception as e:  # noqa: BLE001
                    lines.append("  xref=%d  bbox failed: %s" % (xref, e))
                    continue
                lines.append("  xref=%d  bbox=(%.0f, %.0f, %.0f, %.0f)  w=%.0f h=%.0f"
                             % (xref, bb.x0, bb.y0, bb.x1, bb.y1, bb.width, bb.height))
        except Exception as e:  # noqa: BLE001
            lines.append("  image scan failed: %s" % e)
    path = os.path.join(work, "candidates.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def crop(doc, work, spec, dpi=175, max_w=1150, quality=82):
    from PIL import Image

    meta = {}
    for key, val in spec.items():
        n = int(key)
        page_no, x0, y0, x1, y1 = val
        page = doc[page_no - 1]
        clip = fitz.Rect(x0, y0, x1, y1)
        pix = page.get_pixmap(clip=clip, dpi=dpi)
        im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        if im.width > max_w:
            im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
        path = os.path.join(work, "fig%d.jpg" % n)
        im.save(path, "JPEG", quality=quality, optimize=True)
        meta[n] = {"page": page_no, "box": [x0, y0, x1, y1],
                   "w": im.width, "h": im.height, "bytes": os.path.getsize(path)}

    with open(os.path.join(work, "figmeta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return meta


def b64(path):
    with open(path, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("ascii")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--work", default="./work")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--detect", action="store_true")
    g.add_argument("--crop")
    ap.add_argument("--dpi", type=int, default=175)
    ap.add_argument("--max-width", type=int, default=1150)
    ap.add_argument("--quality", type=int, default=82)
    args = ap.parse_args()

    os.makedirs(args.work, exist_ok=True)
    doc = fitz.open(args.pdf)

    if args.detect:
        t = dump_text(doc, args.work)
        c = detect(doc, args.work)
        print("text  ->", t)
        print("pages ->", os.path.join(args.work, "pageNN.png"))
        print("bboxes->", c)
        print("\nOpen the pageNN.png renders, pick ONE box per figure, then re-run with --crop.")
    else:
        with open(args.crop, encoding="utf-8") as f:
            spec = json.load(f)
        meta = crop(doc, args.work, spec, args.dpi, args.max_width, args.quality)
        for n in sorted(meta):
            m = meta[n]
            print("fig%d  page %d  %dx%d  %.0f KB" % (n, m["page"], m["w"], m["h"], m["bytes"] / 1024))
        print("\nInline as data URI with:  data:image/jpeg;base64,<b64>")


if __name__ == "__main__":
    main()
