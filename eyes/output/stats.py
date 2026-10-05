"""Session statistics — per-category counters + traffic totals."""

import collections

from eyes.core import i18n
from eyes.modules.bandwidth import STATS as BW_STATS


def session_stats(store):
    tr = i18n.TR
    with store.lock:
        cats = collections.Counter(cat for _, (txt, cat) in store.entries.items())
        total = len(store.entries)
    lines = [f"### {tr['stats_header']}"]
    order = ["success", "warning", "error", "masked", "own"]
    for c in order:
        name = tr["categories"].get(c, c).upper()
        lines.append(f"{name:<16}: {cats.get(c, 0)}")
    lines.append(f"{'TOTAL LOGS':<16}: {total}")
    rx_mb = BW_STATS["total_rx"] / (1024 * 1024)
    tx_mb = BW_STATS["total_tx"] / (1024 * 1024)
    lines.append(f"{'TRAFFIC RX/TX':<16}: {rx_mb:.2f} MB / {tx_mb:.2f} MB since start")
    return "\n".join(lines)
