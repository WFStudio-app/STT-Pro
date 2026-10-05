"""Snapshot builder — assembles all collectors into one full log text."""

import socket

from eyes.core import i18n
from eyes.core.version import VERSION
from eyes.modules.collectors import (collect_arp, collect_connections,
                                     collect_dns, collect_interfaces,
                                     collect_routes)
from eyes.modules.pinger import ping_check
from eyes.utils.shell import run


def build_full_log():
    tr = i18n.TR
    parts = [
        f"{tr['title']} v{VERSION} | lang={i18n.LANG}",
        f"{tr['os_info']}: Linux, kernel {run(['uname', '-r']).strip()}",
        f"{tr['hostname']}: {socket.gethostname()}",
        "",
        collect_interfaces(),
        "",
        collect_dns(),
        "",
    ]
    routes_txt, gw = collect_routes()
    parts += [routes_txt, "", collect_arp(), "", collect_connections(), "",
              ping_check(gw)]
    return "\n".join(parts)
