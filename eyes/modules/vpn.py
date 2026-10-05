"""VPN / hidden-traffic detector.

Checks for tunnel interfaces (tun/tap/wg/ppp), default-route changes via
those tunnels, known VPN ports in active connections, and public-IP mismatch
is out of scope (offline tool). Any hit is reported so classify marks it
masked (orange).
"""

import os
import re

from eyes.core import i18n
from eyes.utils.shell import run

_TUNNEL_PAT = re.compile(r"^(tun|tap|wg|ppp|ovpn|utun|ipsec|dsa)", re.I)
_VPN_PORTS = {500: "IKE/IPsec", 4500: "NAT-T/IPsec", 1194: "OpenVPN",
              1198: "OpenVPN", 51820: "WireGuard", 1701: "L2TP",
              1723: "PPTP", 993: "?", 443: "possible TLS tunnel"}


def detect_vpn():
    tr = i18n.TR
    lines = [f"### {tr['vpn_header']}"]
    hits = []

    ifaces = sorted(os.listdir("/sys/class/net")) if os.path.isdir("/sys/class/net") else []
    tunnels = [i for i in ifaces if _TUNNEL_PAT.match(i)]
    for t in tunnels:
        kind = ("WireGuard" if t.startswith("wg") else
                "OpenVPN/TUN" if t.startswith(("tun", "ovpn")) else
                "PPPoE/L2TP" if t.startswith("ppp") else "IPsec/tunnel")
        hits.append(f"Tunnel interface [{t}] detected ({kind}) — traffic may be hidden behind VPN")

    routes = run(["ip", "route", "show"])
    gw_dev = ""
    for row in routes.splitlines():
        m = re.match(r"default via \S+ dev (\S+)", row)
        if m:
            gw_dev = m.group(1)
    if _TUNNEL_PAT.match(gw_dev):
        hits.append(f"Default route goes through tunnel device '{gw_dev}' — ALL traffic is VPN-routed")

    ss = run(["ss", "-tunp"])
    for port, name in _VPN_PORTS.items():
        if re.search(rf"[:.]{port}\b", ss):
            hits.append(f"Active connection on port {port} ({name}) — possible VPN/proxy traffic")

    if hits:
        lines.extend("- " + h for h in hits)
    else:
        lines.append("No VPN / tunnel indicators found (clean direct connection)")
    return "\n".join(lines)
