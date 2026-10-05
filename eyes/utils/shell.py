"""Shared subprocess helper for collectors."""

import subprocess


def run(cmd_list, timeout=10):
    """Run a command, return stdout text ('' on failure). Never raises."""
    try:
        out = subprocess.run(cmd_list, capture_output=True, text=True,
                             timeout=timeout)
        return out.stdout
    except Exception:
        return ""
