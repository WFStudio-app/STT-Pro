"""/g — scan surrounding networks and list those reachable for requests.

Uses `ip route` + ARP table + ping sweep of the local subnet (bounded) to
show which networks/hosts are available to send queries to.
"""

import ipaddress
import shutil
import socket
import subprocess


def _read_routes():
    nets = []
    try:
        out = subprocess.run(["ip", "-o", "route", "show"],
                             capture_output=True, text=True,
                             timeout=10).stdout
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 1 and "/" in parts[0]:
                try:
                    nets.append(str(ipaddress.ip_network(parts[0], strict=False)))
                except ValueError:
                    pass
            elif parts and parts[0] == "default":
                nets.append("default (internet)")
    except (OSError, subprocess.TimeoutExpired):
        pass
    return nets


def _local_subnet():
    """Best-guess local /24 for the ping sweep."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        net = ipaddress.ip_network(ip + "/24", strict=False)
        return net
    except OSError:
        return None


def _arp_hosts():
    hosts = []
    try:
        out = subprocess.run(["ip", "-o", "neigh", "show"],
                             capture_output=True, text=True,
                             timeout=10).stdout
        for line in out.splitlines():
            parts = line.split()
            if parts and parts[0].count(".") == 3:
                hosts.append(parts[0])
    except (OSError, subprocess.TimeoutExpired):
        pass
    return hosts


def _ping(ip, timeout=1):
    if not shutil.which("ping"):
        return False
    try:
        r = subprocess.run(["ping", "-c", "1", "-W", str(timeout), ip],
                           capture_output=True, timeout=timeout + 2)
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def scan_networks(sweep_limit=12):
    """Return list of log lines describing reachable networks/hosts."""
    lines = ["[G] NETWORK SCAN — reachable targets for requests"]
    routes = _read_routes()
    lines.append(f"[G] Networks/routes ({len(routes)}):")
    for n in routes:
        lines.append(f"[G]   NET {n}")
    arp = _arp_hosts()
    lines.append(f"[G] ARP neighbors ({len(arp)}):")
    for h in arp[:20]:
        lines.append(f"[G]   HOST {h} (seen in ARP table)")
    net = _local_subnet()
    if net is not None:
        lines.append(f"[G] Ping-sweeping {net} (max {sweep_limit} probes)...")
        alive = 0
        for i, host in enumerate(net.hosts()):
            if i >= sweep_limit:
                break
            if _ping(str(host)):
                alive += 1
                lines.append(f"[G]   ALIVE {host}")
        lines.append(f"[G] Sweep result: {alive} responsive host(s)")
    else:
        lines.append("[G] WARNING: could not determine local subnet for sweep")
    lines.append("[G] SCAN FINISHED — listed targets accept requests")
    return lines
