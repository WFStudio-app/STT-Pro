"""Device source analysis — who sent the signal, OS fingerprint, controller check.

Provides helpers used by snapshot.py to build the DETAIL FIELDS block:
  * device vendor from MAC OUI (small built-in table)
  * controller boards commonly used for radio/network attacks
    (Flipper Zero, HackRF, YARDStick, WiFi Pineapple, ESP32/8266, ...):
    matched by hostname fragments and known USB/vendor signatures
  * OS guess of remote hosts from ARP/TTL data (`ping` + TTL heuristics)
All checks are best-effort and offline-friendly.
"""

import re

from eyes.core import i18n
from eyes.utils.shell import run

# Small OUI -> vendor table (extend freely)
OUI_VENDORS = {
    "dc:a6:32": "Raspberry Pi Trading", "b8:27:eb": "Raspberry Pi Foundation",
    "24:0a:64": "Espressif (ESP32)", "3c:71:bf": "Espressif (ESP32)",
    "5c:cf:7f": "Espressif (ESP8266)", "18:fe:34": "Espressif (ESP32)",
    "ac:cf:85": "Espressif (ESP32)", "d4:d4:da": "Shenzhen TX",
    "00:1c:be": "Continental", "08:00:27": "PCS Systemtechnik (VirtualBox)",
    "00:50:56": "VMware", "00:0c:29": "VMware", "00:15:5d": "Microsoft Hyper-V",
    "f0:18:98": "Apple", "a4:83:e7": "Apple", "cc:08:fb": "Apple",
    "3c:22:fb": "Apple", "90:84:0d": "LEOPOLD",
    "00:1a:62": "Interlog/Pineapple", "aa:bb:bb": "Unknown/test",
}

# Signatures of attack/controller hardware in hostnames or DHCP options
CONTROLLER_PAT = re.compile(
    r"(flipper|hackrf|yardstick|yard|rtlsdr|pineapple|maltron|bash bunny|"
    r"wifi marauder|esp32|esp8266|teensy|rubber ducky|ducky|pwnix)", re.I)

CONTAINER_HINTS = {
    "flipper": "Flipper Zero multi-tool (radio/BadUSB controller)",
    "hackrf": "HackRF SDR transceiver",
    "yardstick": "YARD Stick One / GoodFET RF tool",
    "rtlsdr": "RTL-SDR receiver",
    "pineapple": "WiFi Pineapple (rogue AP controller)",
    "esp32": "ESP32 dev board (possible Marauder/firmware attacker)",
    "esp8266": "ESP8266 dev board",
    "teensy": "Teensy (HID-attack capable)",
    "ducky": "USB Rubber Ducky HID injector",
    "bunny": "Bash Bunny payload injector",
    "marauder": "WiFi Marauder (ESP32 deauth/recon firmware)",
}


def oui_vendor(mac):
    """Return vendor name for a MAC address prefix, or ''."""
    if not mac or mac == "?":
        return ""
    m = mac.lower().replace("-", ":")
    for n in (8, 5):   # try 3-byte then 2-byte OUI
        oui = ":".join(m.split(":")[:n // 2 + 1]) if n == 8 else ":".join(m.split(":")[:2])
        if oui in OUI_VENDORS:
            return OUI_VENDORS[oui]
    return ""


def controller_check(text):
    """Scan arbitrary text (ARP/DNS/hostnames) for controller-board hints."""
    hits = []
    low = text.lower()
    for key, desc in CONTAINER_HINTS.items():
        if key in low:
            hits.append(desc)
    return hits


def ttl_os(ttl):
    """OS heuristic from IP TTL value."""
    if ttl is None:
        return "?"
    if ttl <= 64:
        return "Linux/macOS/Android/iOS (TTL<=64)"
    if ttl <= 128:
        return "Windows (TTL<=128)"
    return "network gear / BSD / unusual stack (TTL 255)"


def os_fingerprint(ip):
    """Ping a host once, read TTL, return an OS guess string."""
    out = run(["ping", "-c", "1", "-W", "2", ip], timeout=4)
    m = re.search(r"ttl=(\d+)", out, re.I)
    if not m:
        return f"{ip}: no response (filtered/offline)"
    ttl = int(m.group(1))
    hop_note = ""
    if ttl in (64, 255):
        hop_note = ", ~0 hops away (LAN device)"
    elif ttl in (128, ):
        hop_note = ", Windows on LAN"
    return f"{ip}: TTL={ttl} -> {ttl_os(ttl)}{hop_note}"
