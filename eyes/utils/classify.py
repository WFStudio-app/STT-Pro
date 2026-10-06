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

# Neutral header / informational lines: they carry no security signal and
# must never force a category on their own (bug fix v1.4.1: banner text
# containing "Ctrl+C" was misread as "control+ler" -> 'controller', and
# "State: DOWN" was misread as an interface being down).
_NEUTRAL_PAT = re.compile(
    r"^(stt pro\s*[—-]|operating system:|hostname:|"
    r"sistema operativo:|nombre del host:|### |monitor iniciado|"
    r"monitor started|===== log #)", re.I)

# Explicit "all clear" statements — must never be classified as masked/error
# (bug fix v1.4.1: "VPN: NO" / "No VPN ... found" matched 'vpn' -> masked)
_CLEAR_PAT = re.compile(
    r"^(\s*(vpn|doh|dot|proxy|tunnel)\s*:\s*(no|none|off|n/?a)\b"
    r"|no vpn\b|no anomalies\b|no tunnel\b|clean direct connection"
    r"|sin vpn\b|conexi[oó]n directa limpia)", re.I)

# Inactive / administrative-down interfaces are normal housekeeping info
# (lo, dummy0...), not failures — bug fix v1.5.1: "[lo] State: DOWN" was
# misread as a blocked interface and forced every snapshot to [ERROR].
_NEUTRAL_DOWN_PAT = re.compile(
    r"\[(lo|dummy\d*|tap\d*|veth.*|br-\w+)\]\s+state:\s*down\b"
    r"|\bstate:\s*(inactiv|desactivad)", re.I)

# Patterns that decide the category of a log line
_ERROR_PAT = re.compile(
    r"\b(failed|failure|error|unreachable|timeout|timed out|blocked|denied|"
    r"refused|no response|100% packet loss|query failed)\b"
    r"|\bstate:\s*down\b", re.I)

# "not available / unavailable / empty table" are informational gaps (missing
# tools, empty ARP), not failures — bug fix v1.5.1: they matched 'unavailable'
# inside _ERROR_PAT words and turned every snapshot red. Checked before errors.
_INFO_MISS_PAT = re.compile(
    r"\b(unavailable|not available|empty\b|no .*found|information missing"
    r"|недоступн|no disponible)\b", re.I)
_WARN_PAT = re.compile(
    r"\b(suspicious|unknown|anonym|promisc|spoof|dup(licate)? address|"
    r"high port|unexpected|lost|partial|risk|weak signal|arp spoof|"
    r"port-scan|connection flood|changed|disappeared|"
    r"controller board|flipper zero|hackrf|wifi pineapple|marauder|"
    r"rubber ducky|teensy|"
    r"bound to all interfaces|high traffic)\b", re.I)
_MASKED_PAT = re.compile(
    r"\b(masked|hidden|private|randomized|tunnel|vpn|proxy|obfuscat|"
    r"doh|dot|wireguard|openvpn|ipsec|l2tp|pptp|pppoe|"
    r"stub resolver|traffic is vpn-routed)\b", re.I)
_OWN_PAT = re.compile(
    r"\b(loopback|localhost|own network|your network)\b", re.I)


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
    """Classify a single log line into a category name.
    Returns None for neutral/informational lines (no security signal)."""
    ctx = ctx or {}
    low = line.lower()

    # neutral headers carry no signal -> None (bug fix v1.4.1: banner text
    # "(Ctrl+C to stop logging thread)" matched 'controller' as warning)
    if _NEUTRAL_PAT.search(line.strip()):
        return None

    # inactive housekeeping interfaces (lo/dummy/tap...) -> neutral, not error
    # (bug fix v1.5.1: "[lo] State: DOWN" forced [ERROR] on every snapshot)
    if _NEUTRAL_DOWN_PAT.search(low):
        return None

    # explicit "all clear" statements -> success (bug fix v1.4.1: "VPN: NO"
    # and "No VPN / tunnel indicators found" matched 'vpn' -> masked)
    if _CLEAR_PAT.search(low):
        return "success"

    # "not available / unavailable / empty table" are informational gaps
    # (missing tools, empty ARP), not failures — bug fix v1.5.1: such lines
    # matched _ERROR_PAT and turned every snapshot red. Checked before errors;
    # genuine failures ("FAIL", "Status: FAILED") still classify as error.
    if _INFO_MISS_PAT.search(low) and not re.search(
            r"\bfail(ed)?\b|\berror\b|100% packet loss", low):
        return None

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
        try:
            o2i = int(o2)
        except ValueError:
            continue
        if o1 == "10" or (o1 == "172" and 16 <= o2i <= 31) \
           or (o1 == "192" and o2 == "168") or o1 == "169":
            return "own"

    # special module markers (v1.5.0) — checked BEFORE generic patterns so a
    # Bluetooth "[B] ERROR ..." line stays blue, not red
    if low.startswith("[b]"):          # Bluetooth scan lines -> blue marker
        return "bt"

    if _ERROR_PAT.search(low):
        return "error"
    if _MASKED_PAT.search(low):
        return "masked"
    if _WARN_PAT.search(low):
        return "warning"
    if _OWN_PAT.search(low):
        return "own"

    if low.startswith("[send]") and ("status   : ok" in low or "finished" in low):
        return "success"
    if low.startswith("[cleaner]"):    # cleaner window -> blocked/red
        return "error"
    return None   # neutral/informational line


_SEVERITY = ["bt", "error", "masked", "warning", "own", "success"]


def categorize_full(text):
    """Worst (most severe) category among all lines of a full log entry.
    If no line carries a real signal, the entry is 'success'."""
    cats = {c for c in (classify_line(ln) for ln in text.splitlines()) if c}
    for sev in _SEVERITY:
        if sev in cats:
            return sev
    return "success"


def colorize_log(text, default="success"):
    """Paint every line of a log with its category color.
    Neutral lines (classify_line -> None) fall back to the entry category."""
    out = []
    for line in text.splitlines():
        cat = classify_line(line) if line.strip() else default
        cat = cat or default
        out.append(paint(line, CATEGORY_COLOR.get(cat, CATEGORY_COLOR[default])))
    return "\n".join(out)


def print_filter_status():
    tr = i18n.TR
    if IP_FILTER["nets"]:
        print(paint(f"{tr['filter_on']}: {IP_FILTER['nets'][0]}", C.GREEN))
    else:
        print(paint(tr["filter_off"], C.PURPLE))
