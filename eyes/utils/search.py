"""Search across stored logs by substring or regex (case-insensitive)."""

import re

from eyes.core import i18n


def search_logs(store, pattern):
    tr = i18n.TR
    try:
        rx = re.compile(pattern, re.I)
    except re.error:
        rx = re.compile(re.escape(pattern), re.I)
    hits = []
    with store.lock:
        items = sorted(store.entries.items())
    for n, (text, cat) in items:
        if rx.search(text):
            hits.append((n, cat))
    if not hits:
        return f"{tr['search_none']}: '{pattern}'"
    head = [f"{tr['search_found']}: {len(hits)}"]
    body = [f"  #{n:<4} [{cat.upper():<9}]" for n, cat in hits]
    return "\n".join(head + body)
