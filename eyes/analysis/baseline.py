"""Network baseline — remembers the first snapshot's key facts.

Afterwards every change (new gateway MAC, new DNS server, interface flap) is
reported as suspicious so operators notice network tampering.
"""

import re

from eyes.core import i18n

BASE = None   # dict of learned facts


def _facts(text):
    gw_mac = ""
    m = re.search(r"default via (\S+)", text)
    gw_ip = m.group(1) if m else ""
    m = re.search(re.escape(gw_ip) + r" dev \S+ lladdr ([0-9a-f:]{17})", text)
    if m:
        gw_mac = m.group(1)
    dns = tuple(sorted(re.findall(r"nameserver \S+", text)))
    ifaces = tuple(sorted(set(re.findall(r"^\[(\w+)\]", text, re.M))))
    return {"gw_ip": gw_ip, "gw_mac": gw_mac, "dns": dns, "ifaces": ifaces}


def learn_or_compare(text):
    tr = i18n.TR
    global BASE
    cur = _facts(text)
    lines = [f"### {tr['base_header']}"]
    if BASE is None:
        BASE = cur
        lines.append("Baseline learned from first snapshot "
                     f"(gateway {cur['gw_ip'] or '?'}, {len(cur['dns'])} DNS, "
                     f"{len(cur['ifaces'])} interfaces)")
        return "\n".join(lines), text
    diffs = []
    if cur["gw_ip"] != BASE["gw_ip"]:
        diffs.append(f"suspicious: default gateway changed "
                     f"{BASE['gw_ip'] or '?'} -> {cur['gw_ip'] or '?'}")
    if cur["gw_mac"] and BASE["gw_mac"] and cur["gw_mac"] != BASE["gw_mac"]:
        diffs.append(f"suspicious: gateway MAC changed (possible ARP spoof!) "
                     f"{BASE['gw_mac']} -> {cur['gw_mac']}")
    if set(cur["dns"]) != set(BASE["dns"]):
        diffs.append("suspicious: DNS servers changed: "
                     f"{', '.join(cur['dns']) or '(none)'}")
    new_if = set(cur["ifaces"]) - set(BASE["ifaces"])
    gone_if = set(BASE["ifaces"]) - set(cur["ifaces"])
    if new_if:
        diffs.append("unexpected new interface(s): " + ", ".join(sorted(new_if)))
    if gone_if:
        diffs.append("interface disappeared: " + ", ".join(sorted(gone_if)))
    if diffs:
        lines.extend("- " + d for d in diffs)
    else:
        lines.append("Network matches learned baseline (no changes)")
    return "\n".join(lines), text
