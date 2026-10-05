"""Local port audit — LISTEN sockets parsed straight from /proc/net/{tcp,udp}.

No external tools needed. A service bound to 0.0.0.0 (all interfaces) or an
unexpected high port is flagged for the classifier.
"""

import socket

from eyes.core import i18n

WELL_KNOWN = {20, 21, 22, 23, 25, 53, 80, 110, 123, 143, 443, 465, 587,
              853, 993, 995, 32400, 5353, 137, 138, 139, 631, 500, 4500}


def _hex_ip(h):
    return socket.inet_ntop(socket.AF_INET, bytes.fromhex(h)[::-1]) \
        if len(h) == 8 else h


def _parse(path, proto):
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f.readlines()[1:]:
                c = line.split()
                if len(c) < 4:
                    continue
                local, state = c[1], c[3]
                ip_hex, port_hex = local.rsplit(":", 1)
                if proto == "tcp" and state != "0A":   # 0A = LISTEN
                    continue
                rows.append((_hex_ip(ip_hex), int(port_hex, 16)))
    except OSError:
        pass
    return rows


def collect_ports():
    tr = i18n.TR
    lines = [f"### {tr['ports_header']}"]
    found = False
    for path, proto in (("/proc/net/tcp", "tcp"), ("/proc/net/udp", "udp"),
                        ("/proc/net/tcp6", "tcp6"), ("/proc/net/udp6", "udp6")):
        for ip, port in _parse(path, proto.rstrip("6")):
            found = True
            flag = ""
            if ip in ("0.0.0.0", "::") :
                flag = "  <-- bound to ALL interfaces (0.0.0.0), review"
            elif port not in WELL_KNOWN and port >= 49152:
                flag = "  <-- ephemeral/unexpected listen port, suspicious"
            lines.append(f"{proto.upper():5} {ip}:{port}{flag}")
    if not found:
        lines.append("(no listening sockets visible — may need root)")
    return "\n".join(lines)
