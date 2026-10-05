#!/usr/bin/env python3
"""
net_monitor.py — Eyes of the Network (modular entry point)

Network monitor for Linux. Reads information about the network the device is
connected to (interfaces, IP, DNS, routes, ARP neighbors, connections,
gateway/DNS reachability), logs everything with numbered detailed entries in
the terminal, and lets you open any log with:  <number> open-list
All logs are also saved to logs/session.log.

On startup a beautifully formatted command window (banner) is shown, then
live log updates begin automatically (default interval: 1 second).

Project layout (functions split across files & folders):
    eyes/core/     version.py  — version + update algorithm (X.X.X)
                   i18n.py     — English / Spanish translations
                   colors.py   — ANSI colors & log-category legend
                   logstore.py — numbered thread-safe log storage
    eyes/utils/    classify.py — log classification & IP filter
                   banner.py   — startup command window
                   shell.py    — subprocess helper
    eyes/modules/  collectors.py — interfaces/DNS/routes/ARP/connections
                   pinger.py     — reachability checks
                   snapshot.py   — assembles one full log

Versioning scheme (SemVer-like):
    MAJOR.MINOR.PATCH
      X.0.0 -> Global update        (major rewrite, breaking changes)
      0.X.0 -> Major update         (new features, backward compatible)
      0.0.X -> Mini update          (fixes, small improvements)

Usage:      python3 net_monitor.py            (English, default)
            python3 net_monitor.py --lang es  (Spanish)
Commands:   scan | list | N open-list | /updtime [sec] | /setip [ip|cidr]
            | version | clear | banner | help | quit
"""

import os
import re
import sys
import threading

# make the package importable when run directly from the project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eyes.core import i18n                                    # noqa: E402
from eyes.core.colors import C, paint                         # noqa: E402
from eyes.core.logstore import LogStore, LOG_FILE             # noqa: E402
from eyes.core.version import VERSION, UPDATE_ALGORITHM       # noqa: E402
from eyes.modules.snapshot import build_full_log              # noqa: E402
from eyes.utils.banner import show_banner                     # noqa: E402
from eyes.utils.classify import (IP_FILTER, categorize_full,  # noqa: E402
                                 colorize_log, matches_ip_filter,
                                 parse_filter)

TR = i18n.TR
store = LogStore()
LIVE = {"interval": 1.0, "enabled": True}

HELP_FALLBACK = ("Commands: scan | list | N open-list | /updtime [sec] "
                 "| /setip [ip|cidr] | version | clear | banner | help | quit")


def add_log(text):
    """Filter + store one log. Returns number or None if filtered out."""
    if not matches_ip_filter(text):
        return None
    return store.add(text, categorize_full(text))


def live_loop(stop_event):
    while not stop_event.is_set():
        if LIVE["enabled"]:
            try:
                add_log(build_full_log())
            except Exception as e:
                print(paint(f"live scan error: {e}", C.RED))
        waited = 0.0
        step = 0.25
        while waited < LIVE["interval"] and not stop_event.is_set():
            stop_event.wait(step)
            waited += step


def main():
    global TR
    i18n.set_lang(i18n.detect_lang())
    TR = i18n.TR

    show_banner(LIVE["interval"])
    add_log(build_full_log())

    stop = threading.Event()
    th = threading.Thread(target=live_loop, args=(stop,), daemon=True)
    th.start()

    while True:
        try:
            line = input(paint("\n> ", C.BOLD)).strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue
        low = line.lower()
        parts = line.split()
        cmd = parts[0].lower()

        if cmd in ("quit", "exit"):
            LIVE["enabled"] = False
            stop.set()
            print(TR["exit"])
            break
        elif cmd in ("help", "?"):
            print(HELP_FALLBACK)
            show_banner()
        elif cmd == "banner":
            show_banner()
        elif cmd == "list":
            print(store.listing())
        elif cmd == "version":
            print(f"Eyes of the Network v{VERSION}\n{UPDATE_ALGORITHM}")
        elif cmd == "clear":
            store.clear()
            print(paint("OK", C.GREEN))
        elif cmd == "scan":
            n = add_log(build_full_log())
            if n is None:
                print(paint(TR["skipped"], C.YELLOW))
        elif cmd == "/updtime":
            if len(parts) != 2:
                print(paint(f"{TR['updtime_bad']} (current: {LIVE['interval']}s)", C.RED))
            else:
                try:
                    val = float(parts[1])
                    if val < 0.5:
                        raise ValueError
                    LIVE["interval"] = val
                    print(paint(f"{TR['updtime_set']} {val:g} {TR['sec']}.", C.GREEN))
                except ValueError:
                    print(paint(TR["updtime_bad"], C.RED))
        elif cmd == "/setip":
            if len(parts) != 2:
                print(paint(TR["filter_bad"], C.RED))
            elif not parse_filter(parts[1]):
                print(paint(TR["filter_bad"], C.RED))
            elif not IP_FILTER["nets"]:
                print(paint(TR["filter_off"], C.PURPLE))
            else:
                print(paint(f"{TR['filter_on']}: {IP_FILTER['nets'][0]}", C.GREEN))
        else:
            m = re.match(r"^(\d+)\s+open-list$", low)
            if m:
                n = int(m.group(1))
                entry = store.get(n)
                if entry is None:
                    print(paint(f"{TR['not_found']}: #{n}", C.RED))
                else:
                    text, cat = entry
                    print(colorize_log(text, cat))
                    print(paint(f"\n({TR['log_saved']} {os.path.abspath(LOG_FILE)})", C.DIM))
            else:
                print(paint(HELP_FALLBACK, C.DIM))

    stop.set()


if __name__ == "__main__":
    main()
