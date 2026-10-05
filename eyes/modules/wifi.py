"""Wi-Fi collector — SSID, BSSID, channel/frequency, signal (RSSI), standard.

Uses `iw` (mac80211) first, falls back to `nmcli`. Best-effort: if a tool is
missing the section reports "unavailable". Hidden SSID / weak signal lines are
picked up by classify as suspicious/masked.
"""

import re

from eyes.core import i18n
from eyes.utils.shell import run


def _std_from_freq(freq):
    """Rough 802.11 band guess from frequency in MHz."""
    if freq is None:
        return "?"
    if 2400 <= freq < 2500:
        return "2.4GHz (b/g/n)"
    if 4900 <= freq < 5900:
        return "5GHz (a/n/ac)"
    if freq >= 5900:
        return "6GHz (ax/be)"
    return f"{freq}MHz"


def collect_wifi():
    tr = i18n.TR
    lines = [f"### {tr['wifi_header']}"]

    out = run(["iw", "dev", "link"])
    if out.strip():
        ssid = re.search(r"SSID: (.+)", out)
        bssid = re.search(r"Connected to ([0-9a-f:]{17})", out)
        freq = re.search(r"freq: (\d+)", out)
        sig = re.search(r"signal: (-?[\d.]+)", out)
        f = int(freq.group(1)) if freq else None
        lines.append(f"SSID: {ssid.group(1) if ssid else '<hidden network name>'}")
        lines.append(f"BSSID: {bssid.group(1) if bssid else '?'}")
        lines.append(f"Frequency: {f if f else '?'} MHz | Standard: {_std_from_freq(f)}")
        if sig:
            lines.append(f"Signal (RSSI): {sig.group(1)} dBm")
            try:
                if float(sig.group(1)) < -80:
                    lines.append("Weak signal — possible interference or spoofed AP")
            except ValueError:
                pass
        return "\n".join(lines)

    out = run(["nmcli", "-t", "-f", "ACTIVE,SSID,BSSID,CHAN,FREQ,SIGNAL",
               "device", "wifi", "list", "--rescan", "no"])
    if out.strip():
        for row in out.splitlines()[1:6]:
            p = row.split(":")
            if len(p) >= 6 and p[0] == "yes":
                lines.append(
                    f"ACTIVE SSID: {p[1] or '<hidden>'} | BSSID: {p[2]} "
                    f"| CH: {p[3]} | FREQ: {p[4]} | SIGNAL: {p[5]}%")
        if len(lines) > 1:
            return "\n".join(lines)

    lines.append("Wi-Fi information unavailable (no iw / nmcli)")
    return "\n".join(lines)
