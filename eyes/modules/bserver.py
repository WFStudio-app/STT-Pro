"""eyes/modules/bserver.py — /bserver: extended mode for company-wide /
large network monitoring.

What it does:
  * enumerates local interfaces and their subnets (CIDR);
  * scans each subnet via ARP table + optional nmap fallback;
  * aggregates hosts into a single compact "fleet" report;
  * exposes large-network stats helpers used by the REPL.

All output lines are prefixed with [BSERVER] so the classifier can tag them.
"""

import ipaddress
import re
import socket
import subprocess

from eyes.utils.shell import run


def _iface_subnets():
    """Return list of (iface, cidr) from `ip -o -f inet addr`."""
    out = run(["ip", "-o", "-f", "inet", "addr"])
    subs = []
    for line in out.splitlines():
        m = re.search(r"\d+\.\d+\.\d+\.\d+/\d+", line)
        if not m:
            continue
        iface = line.split()[1] if len(line.split()) > 1 else "?"
        try:
            net = ipaddress.ip_network(m.group(0), strict=False)
        except ValueError:
            continue
        # skip loopback-ish /32 host routes for scanning purposes
        if iface == "lo" or net.prefixlen >= 32:
            continue
        subs.append((iface, str(net)))
    return subs


def _arp_hosts():
    """Parse `ip neigh` -> {ipv4: (mac, state)}."""
    out = run(["ip", "neigh"])
    hosts = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        ip = parts[0]
        mac = None
        state = ""
        for p in parts[1:]:
            if re.match(r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$", p, re.I):
                mac = p
            if p in ("REACHABLE", "STALE", "DELAY", "PROBE", "PERMANENT",
                     "FAILED", "INCOMPLETE"):
                state = p
        if re.match(r"^\d+\.\d+\.\d+\.\d+$", ip):
            hosts[ip] = (mac or "?", state or "?")
    return hosts


def _nmap_subnet(cidr):
    """Optional deep scan when nmap exists; returns list of alive ips."""
    if run(["which", "nmap"]).strip() == "":
        return []
    out = run(["nmap", "-sn", "-T4", "--min-rate", "50", cidr], timeout=60)
    ips = re.findall(r"Nmap scan report for (\d+\.\d+\.\d+\.\d+)", out)
    return ips


def scan_fleet():
    """Build the full large-network report. Returns list of log lines."""
    lines = ["[BSERVER] ===== COMPANY / LARGE-NETWORK SCAN ====="]
    subs = _iface_subnets()
    if not subs:
        lines.append("[BSERVER] NOTE: no routable IPv4 subnets found on this host")
        return lines
    arp = _arp_hosts()
    total = 0
    for iface, cidr in subs:
        lines.append(f"[BSERVER] Subnet {cidr} via {iface}")
        found = []
        for ip, (mac, state) in sorted(arp.items()):
            try:
                if ipaddress.ip_address(ip) in ipaddress.ip_network(cidr):
                    found.append((ip, mac, state))
            except ValueError:
                pass
        nmap_ips = set(_nmap_subnet(cidr))
        seen = {ip for ip, _, _ in found}
        for ip in sorted(nmap_ips - seen):
            found.append((ip, "?", "NMAP"))
        if not found:
            lines.append(f"[BSERVER]   no hosts detected in {cidr}")
        for ip, mac, state in found:
            total += 1
            lines.append(f"[BSERVER]   HOST {ip:<16} MAC {mac:<18} [{state}]")
    lines.append(f"[BSERVER] ===== END OF FLEET REPORT: {total} hosts =====")
    return lines


def fleet_stats(store):
    """Compact stats about [BSERVER] logs currently stored."""
    n_logs = 0
    hosts = set()
    with store.lock:
        items = list(store.entries.values())
    for text, cat in items:
        if "[BSERVER]" in text:
            n_logs += 1
            hosts.update(re.findall(r"HOST\s+(\d+\.\d+\.\d+\.\d+)", text))
    return {"bserver_logs": n_logs, "unique_hosts": len(hosts)}
