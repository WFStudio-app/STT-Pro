"""/blut — Bluetooth scan of nearby devices (bluez: bluetoothctl / hcitool).

Every produced log line starts with a blue [B] marker. If no Bluetooth stack
is available the log reports it as an error (red category).
"""

import shutil
import subprocess


def _run(cmd, timeout=25):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)


def scan_bluetooth():
    """Scan nearby Bluetooth devices. Returns list of log lines ([B] prefixed)."""
    lines = ["[B] BLUETOOTH SCAN STARTED"]
    if not shutil.which("bluetoothctl") and not shutil.which("hcitool"):
        lines.append("[B] ERROR: no Bluetooth stack found "
                     "(install bluez / bluetoothctl)")
        return lines
    # known/paired devices
    if shutil.which("bluetoothctl"):
        rc, out = _run(["bluetoothctl", "devices"])
        devs = [l for l in out.splitlines() if l.startswith("Device ")]
        lines.append(f"[B] Known devices found: {len(devs)}")
        for d in devs[:30]:
            lines.append(f"[B]   {d}")
        # power on + short discovery to refresh list (best effort)
        _run(["bluetoothctl", "--timeout", "12", "scan", "on"], timeout=16)
        rc, out = _run(["bluetoothctl", "devices"])
        devs = [l for l in out.splitlines() if l.startswith("Device ")]
        lines.append(f"[B] Devices after scan: {len(devs)}")
        for d in devs[:30]:
            lines.append(f"[B]   {d}")
    elif shutil.which("hcitool"):
        rc, out = _run(["hcitool", "scan"])
        lines.append("[B] hcitool scan output:")
        lines += [f"[B]   {l}" for l in out.splitlines() if l.strip()]
    lines.append("[B] BLUETOOTH SCAN FINISHED")
    return lines
