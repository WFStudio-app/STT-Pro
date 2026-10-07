"""Snapshot builder — assembles all collectors into one full log text.

Structure of every snapshot:
    1) header (title, OS, hostname)
    2) DETAIL FIELDS block — DNS source | VPN? | SOURCE DEVICE | OS
       (the four fields shown when opening a full log with `N open-list`)
    3) detailed sections (interfaces, wi-fi, dns watch, routes, arp, ports,
       connections, bandwidth, vpn, fingerprint, anomalies, baseline, ping)
"""

import re
import socket

from eyes.analysis import anomalies, baseline, fingerprint
from eyes.core import i18n
from eyes.core.version import VERSION
from eyes.modules import device
from eyes.modules.bserver import scan_fleet
from eyes.modules.bandwidth import collect_bandwidth
from eyes.modules.collectors import (collect_arp, collect_connections,
                                     collect_dns, collect_interfaces,
                                     collect_routes)
from eyes.modules.dns_watch import collect_dns_watch
from eyes.modules.pinger import ping_check
from eyes.modules.ports import collect_ports
from eyes.modules.vpn import detect_vpn
from eyes.modules.wifi import collect_wifi
from eyes.utils.shell import run

# extended-mode flag toggled by /bserver (net_monitor keeps it in sync)
BSERVER_STATE = {"active": False}


def bserver_active():
    return bool(BSERVER_STATE["active"])


def fleet_lines():
    """Fleet report text for inclusion in a snapshot log."""
    return "\n".join(scan_fleet())


def _detail_fields(body_text, gw):
    """Build the 4-field summary block from an already-collected body."""
    tr = i18n.TR
    lines = [f"### {tr['detail_header']}"]

    # --- DNS: which server the answers come from ---------------------------
    resolvers = re.findall(r"nameserver (\S+)", body_text)
    dns_note = ", ".join(resolvers[:3]) if resolvers else "?"
    if any(r.startswith("127.") for r in resolvers):
        dns_note += " (local stub -> masked DoH/DoT possible)"
    lines.append(f"{tr['df_dns']}: {dns_note}")

    # --- VPN?: hidden traffic ---------------------------------------------
    vpn_txt = detect_vpn()
    hidden = "No VPN / tunnel indicators found" not in vpn_txt
    first_hit = next((ln[2:] for ln in vpn_txt.splitlines()[1:]
                      if ln.startswith("- ")), "none detected")
    lines.append(f"{tr['df_vpn']}: {'YES — ' + first_hit if hidden else 'NO'}")

    # --- SOURCE DEVICE: what sent the signal + controller check ------------
    own_mac = ""
    m = re.search(r"^\[\w+\].*lladdr|([0-9a-f:]{17})", body_text, re.M)
    macs = re.findall(r"\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b", body_text.lower())
    ctrl = device.controller_check(body_text)
    dev = "own machine"
    if macs:
        vendor = device.oui_vendor(macs[0])
        dev = f"MAC {macs[0]}" + (f" ({vendor})" if vendor else "")
    if ctrl:
        dev += " || CONTROLLER SIGNATURE: " + "; ".join(ctrl)
    lines.append(f"{tr['df_device']}: {dev}")

    # --- OS?: local os + remote guess --------------------------------------
    kern = run(["uname", "-sr"]).strip()
    os_note = f"local: {kern}"
    if gw:
        fp = device.os_fingerprint(gw)
        os_note += f" | gateway: {fp}"
    lines.append(f"{tr['df_os']}: {os_note}")
    return "\n".join(lines), vpn_txt


def build_full_log():
    tr = i18n.TR
    header = [
        f"{tr['title']} v{VERSION} | lang={i18n.LANG}",
        f"{tr['os_info']}: Linux, kernel {run(['uname', '-r']).strip()}",
        f"{tr['hostname']}: {socket.gethostname()}",
        "",
    ]

    routes_txt, gw = collect_routes()
    body_sections = [
        collect_interfaces(), "",
        collect_wifi(), "",
        collect_dns(), "",
        collect_dns_watch(), "",
        routes_txt, "",
        collect_arp(), "",
        collect_ports(), "",
        collect_connections(), "",
        collect_bandwidth(), "",
        detect_vpn(), "",
        fingerprint.neighbor_os_list(), "",
        anomalies.check_anomalies(), "",
        ping_check(gw),
    ]
    if bserver_active():
        body_sections += ["", fleet_lines()]
    body_text = "\n".join(header + body_sections)

    detail, _vpn = _detail_fields(body_text, gw)
    base_txt, _ = baseline.learn_or_compare(body_text)

    # final log = header + DETAIL FIELDS + all sections + baseline comparison
    return "\n".join(header + [detail, "", *body_sections, "", base_txt])
