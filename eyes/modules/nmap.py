"""eyes/modules/nmap.py — ServerCloud nmap assistant.

Curated catalogue of industrial-grade nmap recipes (host discovery, port
scans, service/TLS audits, vuln scripts, firewall checks, saving/diffing).

Commands are only *executed* when the operator explicitly asks for it
(`/nmap run <key> <target>`); browsing and dry-run preview never touch
the network.  This keeps the feature safe on production networks.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field


@dataclass
class Recipe:
    key: str                      # short id used in commands
    title: str                    # human name
    category: str                 # group shown in /nmap list
    args: list = field(default_factory=list)   # template, %TARGET% replaced
    needs_root: bool = False      # sudo recommended
    note: str = ""                # warning / hint

    def build(self, target: str) -> list:
        return [a.replace("%TARGET%", target) for a in self.args]


CATALOG: list[Recipe] = [
    # ---- host discovery -------------------------------------------------
    Recipe("ping", "Live hosts (ping sweep)", "discovery",
           ["nmap", "-sn", "%TARGET%"],
           note="Example target: 192.168.1.0/24"),
    Recipe("pn", "No ping check (assume up)", "discovery",
           ["nmap", "-Pn", "%TARGET%"],
           note="Useful against firewalls that drop ICMP"),

    # ---- scan types -----------------------------------------------------
    Recipe("syn", "SYN scan (half-open, fast)", "scan-types",
           ["nmap", "-sS", "%TARGET%"], needs_root=True,
           note="sudo required; stealthier than connect"),
    Recipe("connect", "TCP connect scan (no root)", "scan-types",
           ["nmap", "-sT", "%TARGET%"]),
    Recipe("udp", "UDP top-20 ports", "scan-types",
           ["nmap", "-sU", "--top-ports", "20", "%TARGET%"], needs_root=True,
           note="slow; expect false open/filtered results"),
    Recipe("ack", "ACK scan (firewall probing)", "scan-types",
           ["nmap", "-sA", "%TARGET%"], needs_root=True,
           note="maps rulesets, does not find open ports"),

    # ---- ports ----------------------------------------------------------
    Recipe("p3", "Specific ports 22,80,443", "ports",
           ["nmap", "-p", "22,80,443", "%TARGET%"]),
    Recipe("pall", "All 65535 ports", "ports",
           ["nmap", "-p-", "%TARGET%"],
           note="very slow — use -T4 and off-hours"),
    Recipe("ptop100", "Top 100 ports", "ports",
           ["nmap", "--top-ports", "100", "%TARGET%"]),

    # ---- detection ------------------------------------------------------
    Recipe("svc", "Service versions", "detection", ["nmap", "-sV", "%TARGET%"]),
    Recipe("os", "OS detection", "detection",
           ["nmap", "-O", "%TARGET%"], needs_root=True),
    Recipe("aggr", "Aggressive (scripts+version+OS+trace)", "detection",
           ["nmap", "-A", "%TARGET%"], needs_root=True,
           note="intrusive — get written permission first"),
    Recipe("openreason", "Open ports + reasons", "detection",
           ["nmap", "--open", "--reason", "%TARGET%"]),
    Recipe("trace", "Traceroute to server", "detection",
           ["nmap", "--traceroute", "%TARGET%"]),

    # ---- standard scripts ----------------------------------------------
    Recipe("default", "Default script scan (-sC)", "scripts",
           ["nmap", "-sC", "%TARGET%"]),
    Recipe("vuln", "Vulnerability scripts", "scripts",
           ["nmap", "--script", "vuln", "%TARGET%"],
           note="NOISY + potentially dangerous on prod; authorization needed"),

    # ---- service-specific scripts ---------------------------------------
    Recipe("web", "Web audit (title + headers)", "service-scripts",
           ["nmap", "--script", "http-title,http-headers",
            "-p", "80,443", "%TARGET%"]),
    Recipe("ssh", "SSH auth methods", "service-scripts",
           ["nmap", "--script", "ssh-auth-methods", "-p", "22", "%TARGET%"]),
    Recipe("ftp", "FTP anonymous login", "service-scripts",
           ["nmap", "--script", "ftp-anon", "-p", "21", "%TARGET%"]),
    Recipe("tls", "TLS cipher enumeration", "service-scripts",
           ["nmap", "--script", "ssl-enum-ciphers", "-p", "443", "%TARGET%"]),

    # ---- timing / targets / output --------------------------------------
    Recipe("fast", "Timing template T4", "timing",
           ["nmap", "-T4", "%TARGET%"],
           note="careful: use -T2 on fragile/old equipment"),
    Recipe("file", "Targets from file + exclusion", "targets",
           ["nmap", "-iL", "servers.txt", "--exclude", "192.168.1.5"],
           note="target argument ignored here; edit servers.txt first"),
    Recipe("save", "Save all formats (report.nmap/.npcap/.xml)", "output",
           ["nmap", "-oA", "report", "%TARGET%"]),
]

BY_KEY = {r.key: r for r in CATALOG}

DIFF_NOTE = ("Compare scans with: ndiff old.xml new.xml "
             "(save scans first using nmap -oX/-oA)")


def list_lines(color=None):
    """Pretty grouped listing of the catalogue."""
    out, seen = [], []
    for r in CATALOG:
        if r.category not in seen:
            seen.append(r.category)
    for cat in seen:
        out.append(("cat", f"── {cat.upper()} ──"))
        for r in CATALOG:
            if r.category != cat:
                continue
            sudo = " [sudo]" if r.needs_root else ""
            out.append(("item", f"  /nmap run {r.key}{sudo}  →  {' '.join(r.args)}"))
            if r.note:
                out.append(("note", f"      ↳ {r.note}"))
    out.append(("note", DIFF_NOTE))
    return out


def preview(key: str, target: str):
    r = BY_KEY.get(key)
    if not r:
        return None
    return r.build(target)


def available() -> bool:
    return shutil.which("nmap") is not None


def run(key: str, target: str, timeout: int = 600):
    """Execute recipe (blocking). Returns (exit_code, output_lines)."""
    cmd = preview(key, target)
    if cmd is None:
        return 2, [f"Unknown recipe '{key}'. Use '/nmap list'."]
    if not available():
        return 127, ["nmap binary not found. Install: "
                     "apt install nmap / dnf install nmap / brew install nmap"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        lines = (p.stdout or "").splitlines() + (p.stderr or "").splitlines()
        return p.returncode, lines[:400]
    except subprocess.TimeoutExpired:
        return 124, [f"Scan aborted after {timeout}s (use /nmap timeout <sec>)"]
    except OSError as e:
        return 1, [str(e)]
