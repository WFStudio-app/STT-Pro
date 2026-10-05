"""File sending over the network (/onuwifi [path] <dest-ip>).

The file is transmitted through a local UDP socket to the destination IP
(port 9988). A transfer log with summary (bytes / packets / time / speed /
status) is produced and returned for the main log store.
"""

import os
import socket
import time

CHUNK = 4096


def send_file(path, dest_ip=None, port=9988):
    """Send file 'path' to dest_ip via UDP chunks. Returns (ok, log_text)."""
    if not os.path.isfile(path):
        return False, (f"[SEND] ERROR: file not found: {path}")
    if not dest_ip:
        return False, ("[SEND] ERROR: destination IP required. "
                       "Usage: /onuwifi <path-to-file> <destination-ip>")
    size = os.path.getsize(path)
    name = os.path.basename(path)
    t0 = time.time()
    sent_bytes = 0
    packets = 0
    status = "OK"
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        with open(path, "rb") as f:
            header = f"EON-FILE:{name}:{size}".encode("utf-8", "replace")
            sock.sendto(header, (dest_ip, port))
            while True:
                chunk = f.read(CHUNK)
                if not chunk:
                    break
                sock.sendto(chunk, (dest_ip, port))
                sent_bytes += len(chunk)
                packets += 1
        sock.sendto(b"EON-END", (dest_ip, port))
        sock.close()
    except OSError as e:
        status = f"FAILED ({e})"
    dt = max(time.time() - t0, 0.001)
    speed = sent_bytes / dt
    ok = status == "OK"
    lines = [
        "[SEND] FILE TRANSFER OVER NETWORK",
        f"[SEND] File     : {name}",
        f"[SEND] Path     : {os.path.abspath(path)}",
        f"[SEND] Size     : {size} bytes",
        f"[SEND] Destination: {dest_ip or 'local broadcast test'}:{port}",
        f"[SEND] Sent     : {sent_bytes} bytes in {packets} packet(s)",
        f"[SEND] Time     : {dt:.3f}s | Speed: {speed:,.0f} B/s",
        f"[SEND] Status   : {status}",
    ]
    return ok, "\n".join(lines)
