"""DNS collector — which DNS server answers our queries.

Resolves a probe domain through every configured resolver (/etc/resolv.conf)
and reports the source server of each answer (DNS: from which server).
DoH/DoT/masked resolvers (127.0.0.x, 9.9.9.9 Quad9, 1.1.1.1 Cloudflare) are
labelled so the classifier can mark them masked/suspicious.
"""

import re
import socket

from eyes.core import i18n

PROBE = "example.com"

_KNOWN = {
    "1.1.1.1": "Cloudflare", "1.0.0.1": "Cloudflare",
    "8.8.8.8": "Google", "8.8.4.4": "Google",
    "9.9.9.9": "Quad9", "149.112.112.112": "Quad9",
    "208.67.222.222": "OpenDNS", "208.67.220.220": "OpenDNS",
}


def _resolvers():
    servers = []
    try:
        with open("/etc/resolv.conf", encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.match(r"\s*nameserver\s+(\S+)", line)
                if m:
                    servers.append(m.group(1))
    except OSError:
        pass
    return servers


def _query(server, host):
    """Minimal UDP DNS query; returns list of answer IPs or None on failure."""
    tid = 0xBEEF
    qname = b"".join(bytes([len(p)]) + p.encode() for p in host.split(".")) + b"\x00"
    pkt = tid.to_bytes(2, "big") + b"\x01\x00\x00\x01\x00\x00\x00\x00" + qname + b"\x00\x01\x00\x01"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2.0)
        s.sendto(pkt, (server, 53))
        data, _ = s.recvfrom(2048)
        s.close()
        ancount = int.from_bytes(data[6:8], "big")
        answers, i = [], len(data) - ancount * 6
        # naive: scan trailing A records (last 4-byte chunks preceded by \xc0\x0c)
        for k in range(len(data) - 16):
            if data[k:k + 10] == b"\xc0\x0c\x00\x01\x00\x01" and int.from_bytes(data[k + 8:k + 10], "big") == 4:
                answers.append(".".join(str(b) for b in data[k + 10:k + 14]))
        return answers[:4] if answers else ["(no A record)"]
    except OSError:
        return None


def collect_dns_watch():
    tr = i18n.TR
    lines = [f"### {tr['dnswatch_header']}"]
    servers = _resolvers()
    if not servers:
        lines.append("No nameservers found in /etc/resolv.conf")
        return "\n".join(lines)
    for srv in servers[:5]:
        tag = _KNOWN.get(srv, "")
        local = srv.startswith(("127.", "::1", "0:0:0:0:0:0:0:1"))
        src = ("LOCAL stub resolver (possible DoH/DoT proxy — masked DNS)"
               if local else f"remote resolver{' (' + tag + ')' if tag else ''}")
        ans = None if local else _query(srv, PROBE)
        if local:
            detail = "not queried directly (loopback)"
        elif ans:
            detail = f"{PROBE} -> {', '.join(ans)}"
        else:
            detail = f"{PROBE} query FAILED / timeout"
        lines.append(f"DNS server {srv}: {src} | {detail}".rstrip())
    return "\n".join(lines)
