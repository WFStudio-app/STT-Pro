#!/usr/bin/env python3
"""
net_monitor.py — Eyes of the Network

Network monitor for Linux. Reads information about the network the device is
connected to (interfaces, IP, DNS, routes, ARP neighbors, connections,
gateway/DNS reachability), logs everything with numbered detailed entries in
the terminal, and lets you open any log with the command:  <number> open-list
All logs are also saved to logs/session.log.

On startup a beautifully formatted command window (banner) is shown, then
live log updates begin automatically (default interval: 1 second).

Versioning scheme (SemVer-like):
    MAJOR.MINOR.PATCH
      MAJOR (X.0.0) -> Global update        (breaking changes / full rewrite)
      MINOR (0.X.0) -> Major feature update (new features, backward compatible)
      PATCH (0.0.X) -> Mini update          (bug fixes, small tweaks)

Usage:      python3 net_monitor.py            (English, default)
            python3 net_monitor.py --lang es  (Spanish)
Stop:       Ctrl+C
Commands:   N open-list     — show full log #N
            list            — list all logs
            /updtime [sec]  — set log update interval (seconds)
            /setip [ip|cidr]— filter logs by IP or network (e.g. 192.168.1.7
                              or 192.168.1.0/24); '/setip off' disables
            version         — current version + update algorithm
            help | banner   — show the command window again
            quit            — exit
"""

import ipaddress
import os
import re
import shutil
import sys
import socket
import subprocess
import threading
from datetime import datetime

# ----------------------------------------------------------------------
# Version & update algorithm
# ----------------------------------------------------------------------
VERSION_MAJOR = 1   # X.0.0 — Global update
VERSION_MINOR = 2   # 0.X.0 — Major feature update
VERSION_PATCH = 1   # 0.0.X — Mini update (patch)
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
        "started": "Monitor started — live updates every {interval}s.",
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
        "log_saved": "Full log saved to file:",
        "not_found": "Log not found",
        "total_logs": "Total logs",
        "exit": "Exiting. Goodbye!",
        "up": "UP", "down": "DOWN",
        "filter_on": "IP filter active",
        "filter_off": "IP filter disabled — showing all logs",
        "filter_bad": "Invalid IP/network. Example: /setip 192.168.1.7 or /setip 192.168.1.0/24",
        "updtime_set": "Log update interval set to",
        "updtime_bad": "Usage: /updtime <seconds>  (min 0.5s). Example: /updtime 5",
        "skipped": "Log skipped (does not match IP filter)",
        "sec": "second(s)",
        "categories": {
            "success": "SUCCESS", "warning": "SUSPICIOUS", "error": "BLOCKED/FAILED",
            "masked": "MASKED", "own": "OWN NETWORK",
        },
        "banner_commands": [
            ("/updtime [sec]",   "set log refresh interval (default 1s)"),
            ("/setip [ip|cidr]", "filter logs by IP or network ('off' to clear)"),
            ("scan",             "capture a new snapshot right now"),
            ("list",             "numbered list of all captured logs"),
            ("N open-list",      "open the FULL detailed log number N"),
            ("version",          "program version + update algorithm"),
            ("clear",            "clear log history in memory"),
            ("banner",           "show this command window again"),
            ("quit",             "exit"),
        ],
    },
    "es": {
        "title": "Eyes of the Network — Monitor de red para Linux",
        "started": "Monitor iniciado — actualizaciones cada {interval}s.",
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
        "log_saved": "Registro completo guardado en archivo:",
        "not_found": "Registro no encontrado",
        "total_logs": "Registros totales",
        "exit": "Saliendo. ¡Adiós!",
        "up": "ACTIVA", "down": "INACTIVA",
        "filter_on": "Filtro IP activo",
        "filter_off": "Filtro IP desactivado — mostrando todos los registros",
        "filter_bad": "IP/red inválida. Ejemplo: /setip 192.168.1.7 o /setip 192.168.1.0/24",
        "updtime_set": "Intervalo de actualización ajustado a",
        "updtime_bad": "Uso: /updtime <segundos>  (mín 0.5s). Ejemplo: /updtime 5",
        "skipped": "Registro omitido (no coincide con el filtro IP)",
        "sec": "segundo(s)",
        "categories": {
            "success": "ÉXITO", "warning": "SOSPECHOSO", "error": "BLOQUEADO/FALLIDO",
            "masked": "ENMASCARADO", "own": "RED PROPIA",
        },
        "banner_commands": [
            ("/updtime [seg]",   "intervalo de refresco (por defecto 1s)"),
            ("/setip [ip|cidr]", "filtrar por IP o red ('off' para limpiar)"),
            ("scan",             "capturar una nueva instantánea ahora"),
            ("list",             "lista numerada de todos los registros"),
            ("N open-list",      "abrir el registro COMPLETO número N"),
            ("version",          "versión + algoritmo de actualización"),
            ("clear",            "limpiar el historial en memoria"),
            ("banner",           "mostrar esta ventana otra vez"),
            ("quit",             "salir"),
        ],
    },
}
TR = T[LANG]

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "session.log")

# ----------------------------------------------------------------------
# Colors & log categories
#   GREEN    success logs
#   YELLOW   suspicious logs
#   RED      blocked / failed / unreachable logs
#   ORANGE   masked logs (private MAC / hidden traffic)
#   PURPLE   your own network (local / loopback / link-local)
# ----------------------------------------------------------------------
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ORANGE = "\033[38;5;208m"
    PURPLE = "\033[35m"
    BLUE = "\033[94m"

CATEGORY_COLOR = {
    "success": C.GREEN,
    "warning": C.YELLOW,
    "error": C.RED,
    "masked": C.ORANGE,
    "own": C.PURPLE,
}

PRIVATE_MAC_OUI = {
    "96:00", "da:0b", "e6:ec", "f6:a9", "76:cf", "3a:52", "22:e7", "ba:8c",
    "02:42", "00:05:50", "fe:ff",
}


def color_enabled():
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("FORCE_COLOR") is not None:
        return True
    return sys.stdout.isatty()


USE_COLOR = color_enabled()


def paint(text, color):
    if not USE_COLOR or not color:
        return text
    return f"{color}{text}{C.RESET}"


def strip_ansi(text):
    return re.sub(r"\033\[[0-9;]*m", "", text)


# ----------------------------------------------------------------------
# Log storage
# ----------------------------------------------------------------------
class LogStore:
    def __init__(self):
        self.entries = {}          # number -> (text, category)
        self.counter = 0
        self.lock = threading.Lock()
        os.makedirs(LOG_DIR, exist_ok=True)

    def add(self, text, category="success"):
        """Add a numbered log entry. Returns number or None if filtered out."""
        with self.lock:
            self.counter += 1
            n = self.counter
            self.entries[n] = (text, category)
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cat_label = TR["categories"][category]
        header = f"===== LOG #{n} | {stamp} | [{cat_label}] ====="
        colored_header = paint(header, CATEGORY_COLOR[category] + C.BOLD
                               if USE_COLOR else "")
        body_colored = colorize_log(text)
        print(colored_header)
        print(body_colored)
        sys.stdout.flush()
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(strip_ansi(header + "\n" + text + "\n\n"))
        return n

    def get(self, n):
        return self.entries.get(n)

    def listing(self):
        with self.lock:
            keys = sorted(self.entries.keys())
        lines = [paint(f"{TR['total_logs']}: {len(keys)}", C.CYAN)]
        for k in keys:
            text, cat = self.entries[k]
            first = text.strip().splitlines()[0] if text else ""
            label = TR["categories"][cat][:4]
            lines.append(paint(f"  #{k} [{label:^10}]", CATEGORY_COLOR[cat])
                         + f" {first[:60]}")
        return "\n".join(lines)

    def clear(self):
        with self.lock:
            self.entries.clear()


store = LogStore()

# ----------------------------------------------------------------------
# IP filter  (/setip)
# ----------------------------------------------------------------------
IP_FILTER = {"nets": []}   # list of ipaddress networks


def parse_filter(spec):
    """Parse '192.168.1.7', '192.168.1.0/24' or 'off'. True=ok, False=bad."""
    global IP_FILTER
    if spec.lower() in ("off", "none", "all", "reset"):
        IP_FILTER["nets"] = []
        return True
    try:
        if "/" in spec:
            net = ipaddress.ip_network(spec, strict=False)
        else:
            net = ipaddress.ip_network(spec + "/32", strict=False)
        IP_FILTER["nets"] = [net]
        return True
    except ValueError:
        return False


def matches_ip_filter(text):
    """True if any IP inside the log falls into the configured network."""
    nets = IP_FILTER["nets"]
    if not nets:
        return True
    for ip in re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b|\b[0-9a-fA-F:]+:[0-9a-fA-F:]+\b", text):
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            continue
        for net in nets:
            if addr.version == net.version and addr in net:
                return True
    return False


def own_ips():
    """All IPs assigned to this machine."""
    ips = set()
    out = run(["ip", "-br", "addr", "show"])
    for row in out.splitlines():
        parts = row.split()
        if len(parts) >= 3:
            ips.add(parts[2].split("/")[0])
    return ips


# ----------------------------------------------------------------------
# Classification & per-line colorization
# ----------------------------------------------------------------------
def classify_line(line, ctx):
    low = line.lower()
    # Neutral lines: headers, banners, separators — never decide the color.
    stripped = line.strip()
    if not stripped:
        return "neutral"
    if stripped.startswith("#") or stripped.startswith("###"):
        return "neutral"
    if any(ch in stripped for ch in "║╔╚╠═"):
        return "neutral"
    if low.startswith("eyes of the network") or low.startswith("monitor iniciado"):
        return "neutral"
    # PURPLE — own network (local/loopback/link-local/machine's own IPs)
    if any(k in low for k in ("lo ", "loopback", "::1", "127.0.0.",
                              "10.", "172.16.", "192.168.", "169.254.",
                              "fe80", "myself", "own")):
        return "own"
    # RED — blocked / failed / didn't reach
    if any(k in low for k in ("fail", "blocked", "denied", "unreachable",
                              "refused", "timeout", "timed out", "no route",
                              "permits", " ! ", "offline", "down")) \
            or "FAIL" in line:
        return "error"
    # ORANGE — masked (locally-administered/private MAC, hidden/anonymized)
    m = re.search(r"([0-9a-f]{2}:){5}[0-9a-f]{2}", low)
    if m:
        mac = m.group(0)
        if mac[0] in "26ea" and mac[1] in "26ae":  # locally administered bit
            return "masked"
        if any(mac.startswith(p) for p in PRIVATE_MAC_OUI):
            return "masked"
    if any(k in low for k in ("hidden", "masked", "anonym", "random",
                              "private", "tunnel", "obfusc")):
        return "masked"
    # YELLOW — suspicious
    if any(k in low for k in ("suspicious", "unknown", "incomplete", "stale",
                              "probe", "scan", "port ", "promisc", "duplicate",
                              "retrans", "lost", "% packet loss")):
        return "warning"
    # GREEN — success
    if any(k in low for k in ("ok", "up", "established", "received", "active",
                              "assigned", "reachable", "connected", "online")):
        return "success"
    return ctx.default


def colorize_log(text, default="success"):
    """Return text with each line painted by its category."""
    class _Ctx:
        pass
    ctx = _Ctx()
    ctx.default = default
    out_lines = []
    for line in text.splitlines():
        cat = classify_line(line, ctx)
        if cat == "neutral":
            out_lines.append(line)
            continue
        out_lines.append(paint(line, CATEGORY_COLOR[cat]))
    return "\n".join(out_lines)


def categorize_full(text):
    """Overall category of a log = the most informative (characteristic)
    line inside it.  Neutral header lines are ignored, so a normal snapshot
    is SUCCESS (green), while snapshots containing failures / masked MACs /
    own-network traffic get the corresponding color."""
    class _Ctx:
        default = "neutral"
    ctx = _Ctx()
    priority = ["error", "masked", "warning", "own", "success"]
    for line in text.splitlines():
        cat = classify_line(line, ctx)
        if cat == "neutral":
            continue
        return cat
    return "success"


# ----------------------------------------------------------------------
# Banner — beautiful command window shown at startup
# ----------------------------------------------------------------------
def show_banner():
    width = min(shutil.get_terminal_size((78, 24)).columns, 78)
    inner = width - 4
    cmds = TR["banner_commands"]
    cmd_w = max(len(c) for c, _ in cmds) + 2

    def hline(l, m, r):
        return l + m * (width - 2) + r

    eye = [
        r"  ______                    __        __   _                  ",
        r" |  ____|                   \ \      / /  | |                 ",
        r" | |__   ___  ___ _   _  ___ \ \ /\ / /_ _| |_ ___  _ __ ___ ",
        r" |  __| / _ \/ __| | | |/ __| \ V  V / _` | __/ _ \| '__/ _ \\",
        r" | |___| (_) \__ \ |_| |\__ \  \ /\ / (_| | || (_) | | |  __/",
        r" |______\___/|___/\__,_||___/   V  V \__,_|\__\___/|_|  \___|",
    ]
    print(paint("\n".join(eye), C.CYAN + C.BOLD))
    print(paint(hline("╔", "═", "╗").center(width), C.BLUE))
    title = f" v{VERSION}  |  {TR['title']}  |  lang={LANG.upper()} "
    print(paint(("║" + title.center(inner) + "║"), C.BLUE))
    print(paint(hline("╠", "═", "╣").center(width), C.BLUE))
    legend = " ".join(
        paint(f"■ {TR['categories'][k]}", CATEGORY_COLOR[k])
        for k in ("success", "own", "warning", "masked", "error"))
    print(paint("║ ", C.BLUE) + legend + paint(" " * max(0, inner - len(strip_ansi(legend)) - 1) + "║", C.BLUE))
    print(paint(hline("╠", "─", "╣").center(width), C.BLUE))
    print(paint("║  " + "COMMANDS:".ljust(inner - 2) + "║", C.BLUE))
    print(paint(hline("╠", "─", "╣").center(width), C.BLUE))
    for cmd, desc in cmds:
        left = paint(" " + cmd, C.BOLD + C.CYAN).ljust(cmd_w + len(paint("", "")))
        # pad without counting ANSI
        left_plain = (" " + cmd).ljust(cmd_w)
        row = "  " + paint(left_plain, C.BOLD + C.CYAN) + " " + paint(desc, C.DIM)
        print(paint("║", C.BLUE) + row.ljust(inner) + paint("║", C.BLUE))
    print(paint(hline("╚", "═", "╝").center(width), C.BLUE))
    print(paint(TR["started"].format(interval=LIVE["interval"]), C.GREEN)
          + "  " + paint("(Ctrl+C to stop logging thread)", C.DIM))


# ----------------------------------------------------------------------
# Command helpers
# ----------------------------------------------------------------------
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
# Live update thread  (default: every 1 second)
# ----------------------------------------------------------------------
LIVE = {"interval": 1.0, "enabled": True}


def add_log(text):
    """Filter + store one log. Returns number or None."""
    if not matches_ip_filter(text):
        return None
    cat = categorize_full(text)
    return store.add(text, cat)


def live_loop(stop_event):
    while not stop_event.is_set():
        if LIVE["enabled"]:
            try:
                add_log(build_full_log())
            except Exception as e:
                print(paint(f"live scan error: {e}", C.RED))
        # sleep in small steps so /updtime takes effect quickly
        waited = 0.0
        step = 0.25
        while waited < LIVE["interval"] and not stop_event.is_set():
            stop_event.wait(step)
            waited += step


# ----------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------
HELP_FALLBACK = (
    "Commands: scan | list | N open-list | /updtime [sec] | /setip [ip|cidr] "
    "| version | clear | banner | help | quit"
)


def main():
    show_banner()

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
            print(TR["help_text"] if "help_text" in TR else HELP_FALLBACK)
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
