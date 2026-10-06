"""Numbered log storage with file persistence for Eyes of the Network."""

import os
import threading
from datetime import datetime

from eyes.core import i18n
from eyes.core.colors import CATEGORY_COLOR, C, paint, strip_ansi

LOG_DIR = os.environ.get("EYES_LOG_DIR", "logs")
LOG_FILE = os.path.join(LOG_DIR, "session.log")


class LogStore:
    """Thread-safe store of numbered log entries: number -> (text, category)."""

    def __init__(self, log_dir=LOG_DIR, log_file=LOG_FILE):
        self.entries = {}          # number -> (text, category)
        self.counter = 0
        self.lock = threading.Lock()
        self.log_dir = log_dir
        self.log_file = log_file
        os.makedirs(self.log_dir, exist_ok=True)

    def trim(self, max_logs=None):
        """Drop the oldest in-memory entries so at most `max_logs` remain.

        max_logs <= 0 or None -> keep everything (no trimming).
        Returns the number of entries removed.
        """
        if not max_logs or int(max_logs) <= 0:
            return 0
        max_logs = int(max_logs)
        with self.lock:
            victims = sorted(self.entries.keys())[:-max_logs]
            for v in victims:
                self.entries.pop(v, None)
        return len(victims)

    def add(self, text, category="success", max_logs=None):
        """Add a numbered log entry, persist to file, return its number.

        After adding, trims the oldest in-memory logs when max_logs is set
        (see /logd command; default 50).
        """
        with self.lock:
            self.counter += 1
            n = self.counter
            self.entries[n] = (text, category)
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n===== LOG #{n} [{stamp}] [{category.upper()}] =====\n")
                f.write(strip_ansi(text))
                if not text.endswith("\n"):
                    f.write("\n")
        except OSError:
            pass
        self.trim(max_logs)
        return n

    def get(self, n):
        with self.lock:
            return self.entries.get(n)

    def clear(self):
        with self.lock:
            self.entries.clear()
            self.counter = 0

    def size_mb(self, n):
        """Size of one log entry in MB (rounded to 3 decimals)."""
        with self.lock:
            entry = self.entries.get(n)
        if entry is None:
            return None
        return round(len(entry[0].encode("utf-8")) / 1024 / 1024, 3)

    def meta(self, n):
        """Full metadata tuple for one log: (name, address, type, size_mb)."""
        with self.lock:
            entry = self.entries.get(n)
        if entry is None:
            return None
        text, cat = entry
        name = text.splitlines()[0][:70] if text else "?"
        addr = self.log_file + f"#LOG{n}"
        size_mb = round(len(text.encode("utf-8")) / 1024 / 1024, 3)
        return {"number": n, "name": name, "address": addr,
                "type": cat.upper(), "size_mb": size_mb}

    def listing(self):
        """Numbered list: [N] (name) (address) (type) (memory MB)."""
        tr = i18n.TR
        with self.lock:
            items = sorted(self.entries.items())
            total = len(items)
            log_file = self.log_file
        lines = []
        for n, (text, cat) in items:
            first = text.splitlines()[0] if text else ""
            name = first[:60]
            addr = f"{log_file}#LOG{n}"
            size_mb = round(len(text.encode("utf-8")) / 1024 / 1024, 3)
            color = CATEGORY_COLOR.get(cat, C.GREEN)
            lines.append(paint(
                f"[{n}] ({name}) ({addr}) ({cat.upper()}) ({size_mb} MB)",
                color))
        lines.append(paint(f"{tr['total_logs']}: {total}", C.BOLD))
        return "\n".join(lines)
