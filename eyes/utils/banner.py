"""Startup command window (banner) — beautiful ASCII box with commands & legend."""

import shutil

from eyes.core import i18n
from eyes.core.colors import CATEGORY_COLOR, C, paint, strip_ansi
from eyes.core.version import VERSION

EYE_ASCII = [
    r"  ______                    __        __   _                  ",
    r" |  ____|                   \ \      / /  | |                 ",
    r" | |__   ___  ___ _   _  ___ \ \ /\ / /_ _| |_ ___  _ __ ___ ",
    r" |  __| / _ \/ __| | | |/ __| \ V  V / _` | __/ _ \| '__/ _ \\",
    r" | |___| (_) \__ \ |_| |\__ \  \ /\ / (_| | || (_) | | |  __/",
    r" |______\___/|___/\__,_||___/   V  V \__,_|\__\___/|_|  \___|",
]


def show_banner(interval=None):
    tr = i18n.TR
    width = min(shutil.get_terminal_size((78, 24)).columns, 78)
    inner = width - 4
    cmds = tr["banner_commands"]
    cmd_w = max(len(c) for c, _ in cmds) + 2

    def hline(l, m, r):
        return l + m * (width - 2) + r

    print(paint("\n".join(EYE_ASCII), C.CYAN + C.BOLD))
    print(paint(hline("╔", "═", "╗").center(width), C.BLUE))
    title = f" v{VERSION}  |  {tr['title']}  |  lang={i18n.LANG.upper()} "
    print(paint(("║" + title.center(inner) + "║"), C.BLUE))
    print(paint(hline("╠", "═", "╣").center(width), C.BLUE))
    legend = " ".join(
        paint(f"■ {tr['categories'][k]}", CATEGORY_COLOR[k])
        for k in ("success", "own", "warning", "masked", "error", "bt"))
    print(paint("║ ", C.BLUE) + legend
          + paint(" " * max(0, inner - len(strip_ansi(legend)) - 1) + "║", C.BLUE))
    print(paint(hline("╠", "─", "╣").center(width), C.BLUE))
    print(paint("║  " + "COMMANDS:".ljust(inner - 2) + "║", C.BLUE))
    print(paint(hline("╠", "─", "╣").center(width), C.BLUE))
    for cmd, desc in cmds:
        left_plain = (" " + cmd).ljust(cmd_w)
        row = "  " + paint(left_plain, C.BOLD + C.CYAN) + " " + paint(desc, C.DIM)
        print(paint("║", C.BLUE) + row.ljust(inner) + paint("║", C.BLUE))
    print(paint(hline("╚", "═", "╝").center(width), C.BLUE))
    if interval is not None:
        print(paint(tr["started"].format(interval=interval), C.GREEN)
              + "  " + paint("(Ctrl+C to stop logging thread)", C.DIM))
