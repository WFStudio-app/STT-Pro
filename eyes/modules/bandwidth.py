"""Bandwidth collector — RX/TX speed per interface from /proc/net/dev.

Keeps previous counters between snapshots; on the first call it only stores
the baseline (speed unknown). Speeds above WARN_BPS are flagged suspicious.
"""

import os
import time

from eyes.core import i18n

_prev = {}          # iface -> (rx_bytes, tx_bytes, timestamp)
STATS = {"total_rx": 0, "total_tx": 0}

WARN_BPS = 10 * 1024 * 1024   # 10 MB/s threshold -> suspicious


def _read_dev():
    res = {}
    try:
        with open("/proc/net/dev", encoding="utf-8") as f:
            for line in f.readlines()[2:]:
                name, _, rest = line.partition(":")
                cols = rest.split()
                if len(cols) >= 9:
                    res[name.strip()] = (int(cols[0]), int(cols[8]))  # rx, tx
    except OSError:
        pass
    return res


def _fmt(bps):
    for unit, div in (("KB/s", 1024), ("MB/s", 1024 ** 2), ("GB/s", 1024 ** 3)):
        if bps < div:
            return f"{bps:.1f} B/s" if unit == "KB/s" else f"{bps / div:.2f} {unit}" \
                if bps < div * 1024 else f"{bps / div:.2f} {unit}"
    return f"{bps / 1024 ** 3:.2f} GB/s"


def collect_bandwidth():
    tr = i18n.TR
    now = time.time()
    cur = _read_dev()
    lines = [f"### {tr['bw_header']}"]
    for iface in sorted(cur):
        rx, tx = cur[iface]
        STATS["total_rx"] += max(0, rx - (_prev.get(iface, (rx, tx, now))[0]))
        STATS["total_tx"] += max(0, tx - (_prev.get(iface, (rx, tx, now))[1]))
        old = _prev.get(iface)
        _prev[iface] = (rx, tx, now)
        if not old or now - old[2] <= 0:
            lines.append(f"[{iface}] RX: — TX: — (baseline)")
            continue
        dt = now - old[2]
        rx_s = max(0, rx - old[0]) / dt
        tx_s = max(0, tx - old[1]) / dt
        note = ""
        if rx_s > WARN_BPS or tx_s > WARN_BPS:
            note = "  <-- HIGH traffic, suspicious"
        lines.append(f"[{iface}] RX: {_fmt(rx_s)} | TX: {_fmt(tx_s)}{note}")
    return "\n".join(lines)
