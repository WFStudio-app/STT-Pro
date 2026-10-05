"""Simple size-based rotation for logs/session.log."""

import os

MAX_BYTES = 2 * 1024 * 1024      # 2 MB per file
KEEP = 3                          # session.log.1 .. .3


def rotate_if_needed(log_file):
    try:
        if not os.path.exists(log_file) or os.path.getsize(log_file) < MAX_BYTES:
            return False
    except OSError:
        return False
    oldest = f"{log_file}.{KEEP}"
    if os.path.exists(oldest):
        os.remove(oldest)
    for i in range(KEEP - 1, 0, -1):
        src, dst = f"{log_file}.{i}", f"{log_file}.{i + 1}"
        if os.path.exists(src):
            os.replace(src, dst)
    os.replace(log_file, f"{log_file}.1")
    return True
