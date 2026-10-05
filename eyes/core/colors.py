"""ANSI colors, log categories & the color legend.

Color code (log categories):
    GREEN    success logs
    YELLOW   suspicious logs
    RED      blocked / failed / unreachable logs
    ORANGE   masked logs (private MAC / hidden traffic)
    PURPLE   your own network (local / loopback / link-local)
"""

import os
import re
import sys


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ORANGE = "\033[38;5;208m"
    PURPLE = "\033[35m"
    BLUE = "\033[94m"


CATEGORY_COLOR = {
    "success": C.GREEN,
    "warning": C.YELLOW,
    "error": C.RED,
    "masked": C.ORANGE,
    "own": C.PURPLE,
}

# category -> CSS-friendly name (used by HTML exporter)
CATEGORY_COLOR_NAME = {
    "success": "success", "warning": "warning", "error": "error",
    "masked": "masked", "own": "own",
}

# OUI prefixes commonly used by randomized / private MAC addresses
PRIVATE_MAC_OUI = {
    "96:00", "da:0b", "e6:ec", "f6:a9", "76:cf", "3a:52", "22:e7", "ba:8c",
    "02:42", "00:05:50", "fe:ff",
}

LEGEND = {
    "en": [
        ("GREEN",  "SUCCESS logs"),
        ("YELLOW", "SUSPICIOUS logs"),
        ("RED",    "BLOCKED / FAILED logs"),
        ("ORANGE", "MASKED logs (private MAC / hidden traffic)"),
        ("PURPLE", "YOUR OWN network (local / loopback)"),
    ],
    "es": [
        ("VERDE",    "registros de ÉXITO"),
        ("AMARILLO", "registros SOSPECHOSOS"),
        ("ROJO",     "registros BLOQUEADOS/FALLIDOS"),
        ("NARANJA",  "registros ENMASCARADOS (MAC privada / tráfico oculto)"),
        ("MORADO",   "tu PROPIA red (local / loopback)"),
    ],
}


def color_enabled():
    """Honor NO_COLOR / FORCE_COLOR conventions and TTY detection."""
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("FORCE_COLOR") is not None:
        return True
    return sys.stdout.isatty()


USE_COLOR = color_enabled()


def paint(text, color):
    if not USE_COLOR or not color:
        return text
    return f"{color}{text}{C.RESET}"


def strip_ansi(text):
    return re.sub(r"\033\[[0-9;]*m", "", text)
