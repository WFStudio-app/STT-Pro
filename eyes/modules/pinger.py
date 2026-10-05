"""Reachability (ping) module — separate file, pluggable into the log builder."""

import re

from eyes.core import i18n
from eyes.utils.shell import run


def ping_check(gateway=None, extra_targets=("8.8.8.8",), count=3, wait=2):
    """Ping gateway + extra targets; returns a text block."""
    tr = i18n.TR
    lines = [f"### {tr['ping_header']}"]
    targets = ([gateway] if gateway else []) + list(extra_targets)
    for t in targets:
        out = run(["ping", "-c", str(count), "-W", str(wait), t])
        recv = re.search(r"(\d+) packets? received", out)
        rtt = re.search(r"=\s*[\d.]+/([\d.]+)/", out)
        ok = recv and int(recv.group(1)) > 0
        status = "OK" if ok else "FAIL (unreachable / blocked)"
        lines.append(
            f"ping {t}: {status} "
            f"(received={recv.group(1) if recv else 0}/{count}, "
            f"avg RTT={rtt.group(1) if rtt else '?'} ms)")
    return "\n".join(lines)
