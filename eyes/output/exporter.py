"""Log exporters — JSON / CSV / HTML report from the LogStore."""

import csv
import html
import io
import json
import os
from datetime import datetime

from eyes.core.colors import CATEGORY_COLOR_NAME


def _rows(store):
    with store.lock:
        items = sorted(store.entries.items())
    return [(n, cat, text) for n, (text, cat) in items]


def export_json(store, path="logs/report.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = [{"number": n, "category": cat, "text": text} for n, cat, text in _rows(store)]
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"generated": datetime.now().isoformat(), "logs": data},
                  f, ensure_ascii=False, indent=2)
    return path


def export_csv(store, path="logs/report.csv"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["number", "category", "text"])
    for n, cat, text in _rows(store):
        w.writerow([n, cat, text.replace("\n", "\\n")])
    with open(path, "w", encoding="utf-8") as f:
        f.write(buf.getvalue())
    return path


_CSS = """
body{background:#111;color:#ddd;font-family:monospace;margin:20px}
h1{color:#7df} .log{border-left:4px solid #555;padding:6px 10px;margin:10px 0;white-space:pre-wrap}
.success{border-color:#3f3}.warning{border-color:#ff3}.error{border-color:#f33}
.masked{border-color:#f80}.own{border-color:#b5f}.bt{border-color:#39f}
.badge{display:inline-block;padding:1px 8px;border-radius:8px;font-size:12px;background:#333}
"""


def export_html(store, path="logs/report.html"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    parts = ["<!doctype html><meta charset='utf-8'>",
             "<title>STT Pro — report</title>",
             f"<style>{_CSS}</style>",
             f"<h1>STT Pro — log report ({datetime.now():%Y-%m-%d %H:%M})</h1>"]
    for n, cat, text in _rows(store):
        color = CATEGORY_COLOR_NAME.get(cat, "success")
        parts.append(f"<div class='log {color}'><span class='badge'>#{n} "
                     f"[{html.escape(cat.upper())}]</span>\n{html.escape(text)}</div>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    return path
