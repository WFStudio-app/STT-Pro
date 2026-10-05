"""Log classification & IP filtering.

Categories (see eyes/core/colors.py):
    success  -> GREEN   | warning -> YELLOW | error -> RED
    masked   -> ORANGE  | own     -> PURPLE
"""

import ipaddress
import re

from eyes.core import i18n
from eyes.core.colors import CATEGORY_COLOR, C, PRIVATE_MAC_OUI, paint

IP_FILTER = {"nets": []}   # list of ipaddress networks (empty = no filter)

# Patterns that decide the category of a log line
_ERROR_PAT = re.compile(
    r"\b(failed|failure|error|unreachable|timeout|timed out|blocked|denied|"
    r"refused|down|no response|100% packet loss)\b", re.I)
_WARN_PAT = re.compile(
    r"\b(suspicious|unknown|anonym|promisc|spoof|dup(licate)? address|"
    r"high port|unexpected|lost|partial|risk)\b", re.I)
_MASKED_PAT = re.compile(
    r"\b(masked|hidden|private|randomized|tunnel|vpn|proxy|obfuscat)\b", re.I)
_OWN_PAT = re.compile(
    r"\b(loopback|lo\b|localhost|own network|your network)\b", re.I)


def parse_filter(spec):
    """Parse '/setip' argument. Returns True on success, False on bad input."""
    if spec.lower() in ("off", "none", "clear"):
        IP_FILTER["nets"] = []
        return True
    try:
        net = ipaddress.ip_network(spec, strict=False)
    except ValueError:
        return False
    IP_FILTER["nets"] = [net]
    return True


def matches_ip_filter(text):
    """True if no filter is set, or at least one IP in text falls inside it."""
    if not IP_FILTER["nets"]:
        return True
    for cand in re.findall(r"\b\d{1,3}(?:\.\d{1,3}){3}\b|\b[0-9a-fA-F:]{5,39}:\b", text):
        try:
            ip = ipaddress.ip_address(cand.strip(":"))
        except ValueError:
            continue
        if any(ip in net for net in IP_FILTER["nets"]):
            return True
    return False


def own_ips():
    """Collect IP addresses assigned to this machine (best effort)."""
    ips = set()
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        for line in socket.gethostbyname_ex(socket.gethostname())[2]:
            ips.add(line)
    except OSError:
        pass
    return ips


def classify_line(line, ctx=None):
    """Classify a single log line into a category name."""
    ctx = ctx or {}
    low = line.lower()

    # MAC with randomized/private OUI -> masked
    for mac in re.findall(r"\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b", low):
        if any(mac.startswith(oui) for oui in PRIVATE_MAC_OUI):
            return "masked"

    # Own / local IPs -> purple
    my = ctx.get("own_ips") or set()
    for cand in re.findall(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", line):
        if cand in my or cand == "127.0.0.1":
            return "own"
        o1, o2 = cand.split(".")[0:2]
        if o1 == "10" or (o1 == "172" and 16 <= int(o2) <= 31) \
           or (o1 == "192" and o2 == "168") or o1 == "169":
            return "own"

    if _ERROR_PAT.search(low):
        return "error"
    if _MASKED_PAT.search(low):
        return "masked"
    if _WARN_PAT.search(low):
        return "warning"
    if _OWN_PAT.search(low):
        return "own"
    return "success"


_SEVERITY = ["error", "masked", "warning", "own", "success"]


def categorize_full(text):
    """Worst (most severe) category among all lines of a full log entry."""
    cats = {classify_line(ln) for ln in text.splitlines() if ln.strip()}
    # neutral banner/header lines should not force 'success' over real signals
    for sev in _SEVERITY:
        if sev in cats:
            return sev
    return "success"


def colorize_log(text, default="success"):
    """Paint every line of a log with its category color."""
    out = []
    for line in text.splitlines():
        cat = classify_line(line) if line.strip() else default
        out.append(paint(line, CATEGORY_COLOR.get(cat, CATEGORY_COLOR[default])))
    return "\n".join(out)


def print_filter_status():
    tr = i18n.TR
    if IP_FILTER["nets"]:
        print(paint(f"{tr['filter_on']}: {IP_FILTER['nets'][0]}", C.GREEN))
    else:
        print(paint(tr["filter_off"], C.PURPLE))
