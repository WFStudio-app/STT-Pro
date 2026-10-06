#!/usr/bin/env python3
"""
net_monitor.py — Eyes of the Network (modular entry point)

Network monitor for Linux. Reads information about the network the device is
connected to (interfaces, Wi-Fi, IP, DNS source, routes, ARP neighbors, ports,
connections, bandwidth, VPN/tunnel detection, OS fingerprints, anomalies),
logs everything with numbered detailed entries in the terminal, and lets you
open any log with:  <number> open-list
All logs are also saved to logs/session.log (with size rotation).

On startup a beautifully formatted command window (banner) is shown, then
live log updates begin automatically (default interval: 1 second, change it
with /updtime). Filter logs by IP/network with /setip.

Project layout (functions split across files & folders):
    eyes/core/     version.py  — version + update algorithm (X.X.X)
                   i18n.py     — English / Spanish translations
                   colors.py   — ANSI colors & log-category legend
                   logstore.py — numbered thread-safe log storage
    eyes/utils/    classify.py — log classification & IP filter
                   banner.py   — startup command window
                   shell.py    — subprocess helper
                   config.py   — persistent config.json
                   search.py   — regex/substring search over logs
    eyes/modules/  collectors.py  — interfaces/DNS/routes/ARP/connections
                   wifi.py        — SSID/BSSID/channel/RSSI
                   bandwidth.py   — RX/TX speed per interface
                   ports.py       — listening-socket audit (/proc/net)
                   dns_watch.py   — which DNS server answers
                   vpn.py         — tunnel / hidden-traffic detection
                   device.py      — OUI vendor, controller boards, TTL->OS
                   pinger.py      — reachability checks
                   snapshot.py    — assembles one full log (+DETAIL FIELDS)
    eyes/analysis/ fingerprint.py — OS guess of neighbors
                   anomalies.py   — port-scan / flood heuristics
                   baseline.py    — learned network profile & drift alerts
    eyes/output/   exporter.py   — JSON / CSV / HTML reports
                   stats.py      — session statistics
                   rotate.py     — log-file rotation

Versioning scheme (SemVer-like X.X.X):
    X.0.0 -> Global update | 0.X.0 -> Major update | 0.0.X -> Mini update

Usage:      python3 net_monitor.py            (English, default)
            python3 net_monitor.py --lang es  (Spanish)
Commands:   scan | list | N open-list | /updtime [sec] | /setip [ip|cidr]
            | stats | export [json|csv|html] | search <text> | config
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
from eyes.modules.transmitter import send_file               # noqa: E402
from eyes.modules.cleaner import run_cleaner                 # noqa: E402
from eyes.modules.blut import scan_bluetooth                 # noqa: E402
from eyes.modules.gscan import scan_networks                 # noqa: E402
from eyes.output.exporter import export_csv, export_html, export_json  # noqa: E402
from eyes.output.rotate import rotate_if_needed               # noqa: E402
from eyes.output.stats import session_stats                   # noqa: E402
from eyes.server.ai_chat import ask_ai, parse_api             # noqa: E402
from eyes.utils import config                                 # noqa: E402
from eyes.utils.banner import show_banner                     # noqa: E402
from eyes.utils.classify import (IP_FILTER, CATEGORY_COLOR, categorize_full,  # noqa: E402
                                 classify_line, colorize_log, matches_ip_filter,
                                 parse_filter)
from eyes.utils.search import search_logs                     # noqa: E402

TR = i18n.TR
store = LogStore()
LIVE = {"interval": 1.0, "enabled": True}
LOGD = {"max": 50}            # /logd: delete oldest logs after every N stored
MODE = {"name": "personal"}   # "personal" | "server" (AI chat extras)
AI = {"base": None, "key": ""}

HELP_FALLBACK = ("Commands: scan | list | N open-list | /linfo [N] | back "
                 "| /updtime [sec] | /setip [ip|cidr] | /onuwifi <file> <ip> "
                 "| /cleaner | /blut | /g | stats | export json|csv|html "
                 "| search <text> | config | version | clear | banner "
                 "| help | quit")


def show_log_info(n):
    """/linfo [N] — full metadata + complete body of one log entry."""
    meta = store.meta(n)
    if meta is None:
        print(paint(f"{TR['not_found']}: #{n}", C.RED))
        return
    entry = store.get(n)
    text, cat = entry
    color = CATEGORY_COLOR.get(cat, C.GREEN)
    print(paint("=" * 60, C.BOLD))
    print(paint(f"[{meta['number']}] ({meta['name']}) "
                f"({meta['address']}) ({meta['type']}) "
                f"({meta['size_mb']} MB)", color))
    print(paint("=" * 60, C.BOLD))
    print(colorize_log(text, cat))
    print(paint(f"\n({TR['log_saved']} {os.path.abspath(LOG_FILE)})", C.DIM))


def add_log(text):
    """Filter + store one log. Returns number or None if filtered out."""
    if not matches_ip_filter(text):
        return None
    n = store.add(text, categorize_full(text), max_logs=LOGD["max"])
    rotate_if_needed(store.log_file)
    return n


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
    config.load()
    lang = config.get("lang") or i18n.detect_lang()
    i18n.set_lang(lang)
    TR = i18n.TR

    try:
        LIVE["interval"] = max(0.5, float(config.get("updtime")))
    except (TypeError, ValueError):
        pass
    try:
        LOGD["max"] = max(0, int(config.get("logd")))
    except (TypeError, ValueError):
        LOGD["max"] = 50
    if config.get("setip"):
        parse_filter(str(config.get("setip")))

    # ---- startup mode selection: personal vs server -------------------
    saved_mode = str(config.get("mode") or "").lower()
    if saved_mode in ("personal", "server"):
        MODE["name"] = saved_mode
        print(paint(i18n.MODE_TEXTS[lang]["chosen_p" if saved_mode != "server" else "chosen_s"], C.CYAN))
    elif sys.stdin.isatty():
        box, t = i18n.mode_window(lang)
        print(paint(box, C.CYAN))
        try:
            choice = input(paint(t["ask"], C.BOLD)).strip()
        except (EOFError, KeyboardInterrupt):
            choice = "1"
        if choice == "2":
            MODE["name"] = "server"
            print(paint(t["chosen_s"], C.PURPLE))
        elif choice in ("1", ""):
            MODE["name"] = "personal"
            print(paint(t["chosen_p"], C.GREEN))
        else:
            MODE["name"] = "personal"
            print(paint(t["bad"], C.YELLOW))
        config.set_and_save("mode", MODE["name"])
    else:
        MODE["name"] = "personal"

    # restore AI API config (server mode)
    if MODE["name"] == "server" and config.get("ai_api"):
        AI["base"], AI["key"] = parse_api(str(config.get("ai_api")))

    # live logging only in an interactive terminal; when input is piped
    # (scripts/tests) the thread would spin unthrottled — use 'scan' cmd
    LIVE["enabled"] = sys.stdin.isatty() and sys.stdout.isatty()

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
        elif cmd == "stats":
            print(session_stats(store))
        elif cmd == "export":
            fmt = parts[1].lower() if len(parts) > 1 else "json"
            fn = {"json": export_json, "csv": export_csv,
                  "html": export_html}.get(fmt)
            if fn is None:
                print(paint("Usage: export [json|csv|html]", C.RED))
            else:
                path = fn(store)
                print(paint(f"OK -> {os.path.abspath(path)}", C.GREEN))
        elif cmd == "search":
            if len(parts) < 2:
                print(paint("Usage: search <text|regex>", C.RED))
            else:
                print(search_logs(store, " ".join(parts[1:])))
        elif cmd == "/linfo":
            if len(parts) < 2:
                print(paint("Usage: /linfo [log number]", C.RED))
            else:
                try:
                    show_log_info(int(parts[1]))
                except ValueError:
                    print(paint("Usage: /linfo [log number]", C.RED))
        elif cmd == "config":
            config.set_and_save("updtime", LIVE["interval"])
            cfg = config.CFG
            print(paint(f"config.json -> {os.path.abspath(config.PATH)}", C.CYAN))
            for k in sorted(cfg):
                v = "***hidden***" if k in config.SECRET_KEYS and cfg[k] else cfg[k]
                print(f"  {k} = {v!r}")
        elif cmd == "back":
            # exit log-reading view -> return to the main command window
            show_banner(LIVE["interval"])
            print(paint(TR["back_ok"], C.CYAN))
        elif cmd == "/onuwifi":
            if len(parts) < 2:
                print(paint(TR["onuwifi_bad"], C.RED))
            else:
                path = parts[1]
                dest = parts[2] if len(parts) > 2 else None
                print(paint(f"[SEND] {TR['onuwifi_sending']} {path}"
                            + (f" -> {dest}" if dest else ""), C.CYAN))
                ok, log_text = send_file(path, dest)
                n = add_log(log_text)
                print(colorize_log(log_text,
                                   "success" if ok else "error"))
                if n is not None:
                    print(paint(f"[{TR['log_num']}] #{n}", C.GREEN))
        elif cmd == "/cleaner":
            print(paint(TR["cleaner_start"], C.YELLOW))
            log_text = run_cleaner()
            n = add_log(log_text)
            print(colorize_log(log_text, "error"))
            if n is not None:
                print(paint(f"[{TR['log_num']}] #{n}", C.GREEN))
        elif cmd == "/blut":
            print(paint(TR["blut_start"], C.BLUE))
            lines = scan_bluetooth()
            log_text = "\n".join(lines)
            n = add_log(log_text)
            for ln in lines:
                cat = classify_line(ln) or "bt"
                print(paint(ln, CATEGORY_COLOR.get(cat, C.BLUE)))
            if n is not None:
                print(paint(f"[{TR['log_num']}] #{n}", C.GREEN))
        elif cmd == "/g":
            print(paint(TR["g_start"], C.CYAN))
            lines = scan_networks()
            log_text = "\n".join(lines)
            n = add_log(log_text)
            print(paint(log_text, C.CYAN))
            if n is not None:
                print(paint(f"[{TR['log_num']}] #{n} | "
                            f"{TR['g_hint']}", C.GREEN))
        elif cmd == "/logd":
            if len(parts) != 2:
                print(paint(f"{TR['logd_bad']} (current: {LOGD['max']})", C.RED))
            else:
                try:
                    val = int(parts[1])
                    if val < 0:
                        raise ValueError
                    LOGD["max"] = val
                    config.set_and_save("logd", val)
                    if val == 0:
                        print(paint(TR["logd_unlimited"], C.PURPLE))
                    else:
                        removed = store.trim(val)
                        msg = f"{TR['logd_set']} {val} {TR['logd_logs']}."
                        if removed:
                            msg += f" ({TR['logd_trimmed']} {removed})"
                        print(paint(msg, C.GREEN))
                except ValueError:
                    print(paint(TR["logd_bad"], C.RED))
        elif cmd == "/ai_api":
            if MODE["name"] != "server":
                print(paint(TR["ai_need_server"], C.RED))
            elif len(parts) != 2:
                print(paint(TR["ai_api_bad"], C.RED))
            elif parts[1].lower() in ("off", "none", "clear"):
                AI["base"], AI["key"] = None, ""
                config.set_and_save("ai_api", "")
                print(paint(TR["ai_api_off"], C.YELLOW))
            else:
                base, key = parse_api(parts[1])
                if not base:
                    print(paint(TR["ai_api_bad"], C.RED))
                else:
                    AI["base"], AI["key"] = base, key
                    config.set_and_save("ai_api", parts[1])
                    n = add_log(f"[AI] API configured -> {base} "
                                f"(key {'set' if key else 'not set'})")
                    print(paint(TR["ai_api_set"], C.GREEN)
                          + (f"  [{TR['log_num']}] #{n}" if n else ""))
        elif cmd == "ask":
            if MODE["name"] != "server":
                print(paint(TR["ai_need_server"], C.RED))
            elif len(parts) < 2:
                print(paint(TR["ask_bad"], C.RED))
            elif not AI["base"]:
                print(paint(TR["ai_no_key"], C.RED))
            else:
                question = " ".join(parts[1:])
                print(paint(TR["ai_thinking"], C.PURPLE))
                ok, answer = ask_ai(AI["base"], AI["key"], store, question)
                log_text = (f"[{TR['ai_log_head']}] Q: {question}\n"
                            f"A: {answer}")
                n = add_log(log_text)
                print(colorize_log(log_text, "success" if ok else "error"))
                if n is not None:
                    print(paint(f"[{TR['log_num']}] #{n}", C.GREEN))
        elif cmd == "/updtime":
            if len(parts) != 2:
                print(paint(f"{TR['updtime_bad']} (current: {LIVE['interval']}s)", C.RED))
            else:
                try:
                    val = float(parts[1])
                    if val < 0.5:
                        raise ValueError
                    LIVE["interval"] = val
                    config.set_and_save("updtime", val)
                    print(paint(f"{TR['updtime_set']} {val:g} {TR['sec']}.", C.GREEN))
                except ValueError:
                    print(paint(TR["updtime_bad"], C.RED))
        elif cmd == "/setip":
            if len(parts) != 2:
                print(paint(TR["filter_bad"], C.RED))
            else:
                off = parts[1].lower() in ("off", "none", "clear")
                if not parse_filter(parts[1]):
                    print(paint(TR["filter_bad"], C.RED))
                else:
                    spec = "" if off or not IP_FILTER["nets"] else parts[1]
                    config.set_and_save("setip", spec)
                    if not IP_FILTER["nets"]:
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
