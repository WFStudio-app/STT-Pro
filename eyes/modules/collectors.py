"""Linux network data collectors (interfaces, DNS, routes, ARP, connections).

Each function returns plain text; the main monitor assembles them into one
numbered log entry. No third-party dependencies — only /sys, `ip`, `ss`.
"""

import os
import re

from eyes.core import i18n
from eyes.utils.shell import run


def collect_interfaces():
    """Parse /sys/class/net + `ip addr` for interfaces, IPs, MAC, state."""
    tr = i18n.TR
    lines = [f"### {tr['iface_header']}"]
    base = "/sys/class/net"
    ifaces = sorted(os.listdir(base)) if os.path.isdir(base) else []
    ip_out = run(["ip", "-br", "addr", "show"])
    for iface in ifaces:
        path = os.path.join(base, iface)
        state = "?"
        try:
            with open(os.path.join(path, "operstate")) as f:
                st = f.read().strip()
            state = tr["up"] if st == "up" else tr["down"]
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
        lines.append(f"[{iface}] {tr['state']}: {state} | {tr['mac']}: {mac}")
        lines.append(f"    {tr['addresses']}: {', '.join(addrs) if addrs else '—'}")
    return "\n".join(lines)


def collect_dns():
    tr = i18n.TR
    lines = [f"### {tr['dns_header']}"]
    try:
        with open("/etc/resolv.conf", encoding="utf-8", errors="replace") as f:
            content = f.read().strip()
        lines.append(content if content else "(empty)")
    except Exception as e:
        lines.append(f"resolv.conf error: {e}")
    return "\n".join(lines)


def collect_routes():
    tr = i18n.TR
    lines = [f"### {tr['routes_header']}"]
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
    lines.append(f"{tr['default_gw']}: {gw or '?'}")
    return "\n".join(lines), gw


def collect_arp():
    tr = i18n.TR
    lines = [f"### {tr['arp_header']}"]
    out = run(["ip", "neigh", "show"])
    if not out:
        out = run(["arp", "-an"])
    lines.append(out.strip() or "(ARP table empty / unavailable)")
    return "\n".join(lines)


def collect_connections():
    tr = i18n.TR
    lines = [f"### {tr['conns_header']}"]
    out = run(["ss", "-tunap"])
    if not out:
        out = run(["netstat", "-tunap"])
    body = out.strip().splitlines()
    lines.extend(body[:60])
    if len(body) > 60:
        lines.append(f"... ({len(body) - 60} more rows)")
    return "\n".join(lines)
