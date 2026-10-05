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

    def add(self, text, category="success"):
        """Add a numbered log entry, persist to file, return its number."""
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
        return n

    def get(self, n):
        with self.lock:
            return self.entries.get(n)

    def clear(self):
        with self.lock:
            self.entries.clear()
            self.counter = 0

    def listing(self):
        """Human-readable numbered list of all stored logs."""
        tr = i18n.TR
        with self.lock:
            items = sorted(self.entries.items())
            total = len(items)
        lines = []
        for n, (text, cat) in items:
            first = text.splitlines()[0] if text else ""
            color = CATEGORY_COLOR.get(cat, C.GREEN)
            lines.append(paint(f"  #{n:<4} [{cat.upper():<9}] {first}", color))
        lines.append(paint(f"{tr['total_logs']}: {total}", C.BOLD))
        return "\n".join(lines)
