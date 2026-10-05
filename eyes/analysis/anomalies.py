"""Anomaly heuristics over connection data.

Rules (offline, no deps):
  * many distinct destination ports from one source -> port scan pattern
  * very high connection count per host -> flood/exhaustion hint
Results are phrased so classify() colors them yellow/red.
"""

import collections
import re

from eyes.core import i18n
from eyes.utils.shell import run


def check_anomalies():
    tr = i18n.TR
    lines = [f"### {tr['anom_header']}"]
    ss = run(["ss", "-tn"])
    dst_ports = collections.defaultdict(set)
    conns = collections.Counter()
    for row in ss.splitlines()[1:]:
        cols = row.split()
        if len(cols) >= 4:
            src, dst = cols[3], cols[4]
            conns[src.rsplit(":", 1)[0]] += 1
            dst_ports[src].add(dst.rsplit(":", 1)[-1])
    findings = []
    for src, ports in dst_ports.items():
        if len(ports) > 20:
            findings.append(f"suspicious: {src} contacted {len(ports)} different "
                            f"destination ports (port-scan pattern)")
    for host, cnt in conns.items():
        if cnt > 50:
            findings.append(f"suspicious: {host} holds {cnt} TCP connections "
                            "(possible connection flood)")
    if findings:
        lines.extend("- " + f for f in findings)
    else:
        lines.append("No anomalies detected in current traffic pattern")
    return "\n".join(lines)
