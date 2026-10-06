"""Persistent configuration (config.json in project root).

Holds: language, refresh interval, IP filter, thresholds. Loaded at startup,
saved whenever a command changes something. Missing/corrupt file -> defaults.
"""

import json
import os

PATH = os.environ.get("EYES_CONFIG", "config.json")

DEFAULTS = {
    "lang": None,          # None = auto-detect
    "mode": None,          # None = ask at startup | "personal" | "server"
    "updtime": 1.0,
    "setip": "",           # "" = off
    "logd": 50,            # keep last N logs in memory (older deleted); 0 = unlimited
    "ai_api": "",          # server mode: "<key>@<url>" or url or key (never shown in 'config')
    "bw_warn_mbps": 10,
}

SECRET_KEYS = ("ai_api",)

CFG = dict(DEFAULTS)


def load():
    global CFG
    try:
        with open(PATH, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for k in DEFAULTS:
                if k in data:
                    CFG[k] = data[k]
    except (OSError, ValueError):
        pass
    return CFG


def save():
    try:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(CFG, f, indent=2)
    except OSError:
        pass


def get(key):
    return CFG.get(key, DEFAULTS.get(key))


def set_and_save(key, value):
    CFG[key] = value
    save()
