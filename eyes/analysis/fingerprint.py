"""OS fingerprinting of neighbors via ARP table + TTL probing (best effort)."""

import re

from eyes.core import i18n
from eyes.modules.device import os_fingerprint
from eyes.utils.shell import run


def neighbor_os_list(max_hosts=6):
    """Return OS-guess lines for hosts in the ARP table."""
    tr = i18n.TR
    lines = [f"### {tr['fp_header']}"]
    out = run(["ip", "neigh", "show"])
    ips = []
    for row in out.splitlines():
        m = re.match(r"(\d+\.\d+\.\d+\.\d+) dev \S+ ", row)
        if m and m.group(1) not in ips:
            ips.append(m.group(1))
    if not ips:
        lines.append("(no ARP neighbors to fingerprint)")
        return "\n".join(lines)
    for ip in ips[:max_hosts]:
        lines.append("- " + os_fingerprint(ip))
    if len(ips) > max_hosts:
        lines.append(f"... ({len(ips) - max_hosts} more hosts skipped)")
    return "\n".join(lines)
