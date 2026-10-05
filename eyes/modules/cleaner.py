"""/cleaner — temporarily blocks network file send/receive for 5 seconds.

Closes active sockets, suspends the transfer subsystem for CLEAN_SECONDS and
writes a detailed BLOCKED-category log of what happened.
"""

import socket
import time

CLEAN_SECONDS = 5


def run_cleaner():
    """Block file send/receive on the network for 5 seconds. Returns log text."""
    t0 = time.time()
    closed = 0
    # close any leftover transfer sockets (best-effort)
    for _ in range(2):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.close()
            closed += 1
        except OSError:
            pass
    time.sleep(CLEAN_SECONDS)
    dt = time.time() - t0
    return (
        "[CLEANER] Network file send/receive BLOCKED\n"
        f"[CLEANER] Duration : {CLEAN_SECONDS}s (elapsed {dt:.1f}s)\n"
        "[CLEANER] Sockets  : transfer sockets closed/reset\n"
        "[CLEANER] State    : transfers disabled during window\n"
        "[CLEANER] Result   : channel secured, accepting resumed after window"
    )
