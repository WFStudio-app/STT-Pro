#!/usr/bin/env python3
"""
net_monitor.py — Eyes of the Network

Network monitor for Linux. Reads information about the network the device is
connected to (interfaces, IP, DNS, routes, ARP neighbors, connections,
gateway/DNS reachability), logs everything with numbered detailed entries in
the terminal, and lets you open any log with the command:  <number> open-list
All logs are also saved to logs/session.log.

Versioning scheme (SemVer-like):
    MAJOR.MINOR.PATCH
      MAJOR (X.0.0) -> Global update        (breaking changes / full rewrite)
      MINOR (0.X.0) -> Major feature update (new features, backward compatible)
      PATCH (0.0.X) -> Mini update          (bug fixes, small tweaks)

Usage:      python3 net_monitor.py            (English, default)
            python3 net_monitor.py --lang es  (Spanish)
Stop:       Ctrl+C
Commands:   N open-list  — show full log #N
            list         — list all logs
            version      — current version + update algorithm
            help         — help
            quit         — exit
"""

import os
import re
import sys
import socket
import subprocess
import threading
from datetime import datetime

# ----------------------------------------------------------------------
# Version & update algorithm
# ----------------------------------------------------------------------
VERSION_MAJOR = 1   # X.0.0 — Global update
VERSION_MINOR = 1   # 0.X.0 — Major feature update
VERSION_PATCH = 0   # 0.0.X — Mini update (patch)
VERSION = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"

UPDATE_ALGORITHM = """
Update algorithm:
  X.0.0  ->  Global update   (major rewrite, breaking changes)
  0.X.0  ->  Major update    (new features, backward compatible)
  0.0.X  ->  Mini update     (fixes, small improvements)
  Format:  X.X.X  (MAJOR.MINOR.PATCH)
"""

# ----------------------------------------------------------------------
# i18n — English / Spanish
# ----------------------------------------------------------------------
LANG = os.environ.get("LANG_PREFIX", "en")
if "--lang" in sys.argv:
    try:
        LANG = sys.argv[sys.argv.index("--lang") + 1]
    except IndexError:
        pass
if LANG not in ("en", "es"):
    LANG = "en"

T = {
    "en": {
        "title": "Eyes of the Network — Linux network monitor",
        "started": "Monitor started. Commands: scan | list | N open-list | version | clear | help | quit",
        "iface_header": "NETWORK INTERFACES",
        "addresses": "IP addresses",
        "mac": "MAC address",
        "state": "State",
        "dns_header": "DNS CONFIGURATION",
        "routes_header": "IP ROUTING TABLE",
        "arp_header": "ARP NEIGHBORS",
        "conns_header": "ACTIVE TCP/UDP CONNECTIONS",
        "ping_header": "REACHABILITY CHECK",
        "default_gw": "Default gateway",
        "hostname": "Hostname",
        "os_info": "Operating system",
        "periodic": "Periodic scan finished",
        "log_saved": "Full log saved to file:",
        "not_found": "Log not found",
        "total_logs": "Total logs",
        "help_text": (
            "Commands:\n"
            "  scan          — capture a new network snapshot\n"
            "  list          — numbered list of all captured logs\n"
            "  N open-list   — open the FULL detailed log number N\n"
            "  version       — program version and update algorithm\n"
            "  clear         — clear log history in memory\n"
            "  help          — this help\n"
            "  quit          — exit\n"
        ),
        "exit": "Exiting. Goodbye!",
        "up": "UP", "down": "DOWN",
    },
    "es": {
        "title": "Eyes of the Network — Monitor de red para Linux",
        "started": "Monitor iniciado. Comandos: scan | list | N open-list | version | clear | help | quit",
        "iface_header": "INTERFACES DE RED",
        "addresses": "Direcciones IP",
        "mac": "Dirección MAC",
        "state": "Estado",
        "dns_header": "CONFIGURACIÓN DNS",
        "routes_header": "TABLA DE ENRUTAMIENTO IP",
        "arp_header": "VECINOS ARP",
        "conns_header": "CONEXIONES TCP/UDP ACTIVAS",
        "ping_header": "COMPROBACIÓN DE ALCANCE",
        "default_gw": "Puerta de enlace predeterminada",
        "hostname": "Nombre del host",
        "os_info": "Sistema operativo",
        "periodic": "Escaneo periódico finalizado",
        "log_saved": "Registro completo guardado en archivo:",
        "not_found": "Registro no encontrado",
        "total_logs": "Registros totales",
        "help_text": (
            "Comandos:\n"
            "  scan          — capturar una nueva instantánea de red\n"
            "  list          — lista numerada de todos los registros\n"
            "  N open-list   — abrir el registro COMPLETO y detallado número N\n"
            "  version       — versión del programa y algoritmo de actualización\n"
            "  clear         — limpiar el historial en memoria\n"
            "  help          — esta ayuda\n"
            "  quit          — salir\n"
        ),
        "exit": "Saliendo. ¡Adiós!",
        "up": "ACTIVA", "down": "INACTIVA",
    },
}
TR = T[LANG]

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "session.log")


# ----------------------------------------------------------------------
# Log storage
# ----------------------------------------------------------------------
class LogStore:
    def __init__(self):
        self.entries = {}          # number -> text
        self.counter = 0
        self.lock = threading.Lock()
        os.makedirs(LOG_DIR, exist_ok=True)

    def add(self, text):
        with self.lock:
            self.counter += 1
            n = self.counter
            self.entries[n] = text
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"===== LOG #{n} | {stamp} ====="
        full = header + "\n" + text + "\n"
        print(full)
        sys.stdout.flush()
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(full + "\n")
        return n

    def get(self, n):
        return self.entries.get(n)

    def listing(self):
        with self.lock:
            keys = sorted(self.entries.keys())
        lines = [f"{TR['total_logs']}: {len(keys)}"]
        for k in keys:
            first = self.entries[k].strip().splitlines()[0] if self.entries[k] else ""
            lines.append(f"  #{k}: {first[:70]}")
        return "\n".join(lines)

    def clear(self):
        with self.lock:
            self.entries.clear()


store = LogStore()


def run(cmd_list):
    """Run a shell command, return stdout text ('' on failure)."""
    try:
        out = subprocess.run(cmd_list, capture_output=True, text=True, timeout=10)
        return out.stdout
    except Exception:
        return ""


# ----------------------------------------------------------------------
# Linux data collectors
# ----------------------------------------------------------------------
def collect_interfaces():
    """Parse /sys/class/net + `ip addr` for interfaces, IPs, MAC, state."""
    lines = [f"### {TR['iface_header']}"]
    base = "/sys/class/net"
    ifaces = sorted(os.listdir(base)) if os.path.isdir(base) else []
    ip_out = run(["ip", "-br", "addr", "show"])
    for iface in ifaces:
        path = os.path.join(base, iface)
        state = "?"
        try:
            with open(os.path.join(path, "operstate")) as f:
                st = f.read().strip()
            state = TR["up"] if st == "up" else TR["down"]
        except Exception:
            pass
        mac = ""
        try:
            with open(os.path.join(path, "address")) as f:
                mac = f.read().strip()
        except Exception:
            pass
        addrs = []
        for row in ip_out.splitlines():
            parts = row.split()
            if len(parts) >= 3 and parts[0] == iface:
                addrs.append(f"{parts[2]} ({parts[1]})")
        lines.append(f"[{iface}] {TR['state']}: {state} | {TR['mac']}: {mac}")
        lines.append(f"    {TR['addresses']}: {', '.join(addrs) if addrs else '—'}")
    return "\n".join(lines)


def collect_dns():
    lines = [f"### {TR['dns_header']}"]
    try:
        with open("/etc/resolv.conf", encoding="utf-8", errors="replace") as f:
            content = f.read().strip()
        lines.append(content if content else "(empty)")
    except Exception as e:
        lines.append(f"resolv.conf error: {e}")
    return "\n".join(lines)


def collect_routes():
    lines = [f"### {TR['routes_header']}"]
    out = run(["ip", "route", "show"])
    if not out:
        out = run(["route", "-n"])
    lines.append(out.strip() or "(no routes output)")
    gw = ""
    for row in out.splitlines():
        m = re.search(r"default via (\S+)", row)
        if m:
            gw = m.group(1)
            break
    lines.append(f"{TR['default_gw']}: {gw or '?'}")
    return "\n".join(lines), gw


def collect_arp():
    lines = [f"### {TR['arp_header']}"]
    out = run(["ip", "neigh", "show"])
    if not out:
        out = run(["arp", "-an"])
    lines.append(out.strip() or "(ARP table empty / unavailable)")
    return "\n".join(lines)


def collect_connections():
    lines = [f"### {TR['conns_header']}"]
    out = run(["ss", "-tunap"])
    if not out:
        out = run(["netstat", "-tunap"])
    body = out.strip().splitlines()
    lines.extend(body[:60])
    if len(body) > 60:
        lines.append(f"... ({len(body) - 60} more rows)")
    return "\n".join(lines)


def ping_check(gateway):
    lines = [f"### {TR['ping_header']}"]
    targets = []
    if gateway:
        targets.append(gateway)
    targets.append("8.8.8.8")
    for t in targets:
        out = run(["ping", "-c", "3", "-W", "2", t])
        recv = re.search(r"(\d+) packets? received", out)
        rtt = re.search(r"=\s*[\d.]+/([\d.]+)/", out)
        status = "OK" if recv and int(recv.group(1)) > 0 else "FAIL"
        lines.append(f"ping {t}: {status} "
                     f"(received={recv.group(1) if recv else 0}/3, "
                     f"avg RTT={rtt.group(1) if rtt else '?'} ms)")
    return "\n".join(lines)


def build_full_log():
    parts = [
        f"{TR['title']} v{VERSION} | lang={LANG}",
        f"{TR['os_info']}: Linux, kernel {run(['uname', '-r']).strip()}",
        f"{TR['hostname']}: {socket.gethostname()}",
        "",
        collect_interfaces(),
        "",
        collect_dns(),
        "",
    ]
    routes_txt, gw = collect_routes()
    parts += [routes_txt, "", collect_arp(), "", collect_connections(), "", ping_check(gw)]
    return "\n".join(parts)


# ----------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------
def main():
    print(f"\n*** {TR['title']} v{VERSION} ***")
    print(TR["started"] + "\n")

    store.add(build_full_log())

    stop = threading.Event()

    def periodic():
        while not stop.wait(60):
            try:
                store.add(build_full_log())
                print(f"[{datetime.now():%H:%M:%S}] {TR['periodic']}")
            except Exception as e:
                print(f"periodic scan error: {e}")

    th = threading.Thread(target=periodic, daemon=True)
    th.start()

    while True:
        try:
            line = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue
        low = line.lower()
        if low in ("quit", "exit"):
            print(TR["exit"])
            break
        elif low == "help":
            print(TR["help_text"])
        elif low == "list":
            print(store.listing())
        elif low == "version":
            print(f"Eyes of the Network v{VERSION}\n{UPDATE_ALGORITHM}")
        elif low == "clear":
            store.clear()
            print("OK")
        elif low == "scan":
            store.add(build_full_log())
        else:
            m = re.match(r"^(\d+)\s+open-list$", low)
            if m:
                n = int(m.group(1))
                entry = store.get(n)
                if entry is None:
                    print(f"{TR['not_found']}: #{n}")
                else:
                    print(entry)
                    print(f"\n({TR['log_saved']} {os.path.abspath(LOG_FILE)})")
            else:
                print(TR["help_text"])

    stop.set()


if __name__ == "__main__":
    main()
