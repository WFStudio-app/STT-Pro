"""Internationalization (English / Spanish) for Eyes of the Network.

Usage:
    from eyes.core import i18n
    i18n.set_lang("es")            # or env LANG_PREFIX=es, or --lang es
    print(i18n.TR["title"])
"""

import os
import sys

SUPPORTED = ("en", "es")


def detect_lang(argv=None):
    """Resolve language from CLI (--lang xx) then env (LANG_PREFIX), default 'en'."""
    argv = sys.argv if argv is None else argv
    lang = os.environ.get("LANG_PREFIX", "en")
    if "--lang" in argv:
        try:
            lang = argv[argv.index("--lang") + 1]
        except IndexError:
            pass
    return lang if lang in SUPPORTED else "en"


T = {
    "en": {
        "title": "Eyes of the Network — Linux network monitor",
        "started": "Monitor started — live updates every {interval}s.",
        "iface_header": "NETWORK INTERFACES",
        "addresses": "IP addresses",
        "mac": "MAC address",
        "state": "State",
        "dns_header": "DNS CONFIGURATION",
        "routes_header": "IP ROUTING TABLE",
        "arp_header": "ARP NEIGHBORS",
        "conns_header": "ACTIVE TCP/UDP CONNECTIONS",
        "ping_header": "REACHABILITY CHECK",
        "default_gw": "Default gateway",
        "hostname": "Hostname",
        "os_info": "Operating system",
        "log_saved": "Full log saved to file:",
        "not_found": "Log not found",
        "total_logs": "Total logs",
        "exit": "Exiting. Goodbye!",
        "up": "UP", "down": "DOWN",
        "filter_on": "IP filter active",
        "filter_off": "IP filter disabled — showing all logs",
        "filter_bad": "Invalid IP/network. Example: /setip 192.168.1.7 or /setip 192.168.1.0/24",
        "updtime_set": "Log update interval set to",
        "updtime_bad": "Usage: /updtime <seconds>  (min 0.5s). Example: /updtime 5",
        "skipped": "Log skipped (does not match IP filter)",
        "wifi_header": "WI-FI CONNECTION",
        "bw_header": "BANDWIDTH (RX/TX)",
        "ports_header": "LISTENING PORTS AUDIT",
        "dnswatch_header": "DNS SOURCE WATCH",
        "vpn_header": "VPN / HIDDEN TRAFFIC",
        "fp_header": "DEVICE OS FINGERPRINT",
        "anom_header": "ANOMALY CHECK",
        "base_header": "BASELINE COMPARISON",
        "stats_header": "SESSION STATISTICS",
        "search_found": "Search matches",
        "search_none": "No logs match",
        "detail_header": "DETAIL FIELDS",
        "df_dns": "DNS",
        "df_vpn": "VPN",
        "df_device": "SOURCE DEVICE",
        "df_os": "OS",
        "sec": "second(s)",
        "categories": {
            "success": "SUCCESS", "warning": "SUSPICIOUS", "error": "BLOCKED/FAILED",
            "masked": "MASKED", "own": "OWN NETWORK",
        },
        "banner_commands": [
            ("/updtime [sec]",   "set log refresh interval (default 1s)"),
            ("/setip [ip|cidr]", "filter logs by IP or network ('off' to clear)"),
            ("scan",             "capture a new snapshot right now"),
            ("list",             "numbered list of all captured logs"),
            ("N open-list",      "open the FULL detailed log number N"),
            ("stats",            "session statistics per log color"),
            ("export [json|csv|html]", "export all logs to a file"),
            ("search <text>",    "find logs containing text/regex"),
            ("config",           "show/save persistent config.json"),
            ("version",          "program version + update algorithm"),
            ("clear",            "clear log history in memory"),
            ("banner",           "show this command window again"),
            ("quit",             "exit"),
        ],
    },
    "es": {
        "title": "Eyes of the Network — Monitor de red para Linux",
        "started": "Monitor iniciado — actualizaciones cada {interval}s.",
        "iface_header": "INTERFACES DE RED",
        "addresses": "Direcciones IP",
        "mac": "Dirección MAC",
        "state": "Estado",
        "dns_header": "CONFIGURACIÓN DNS",
        "routes_header": "TABLA DE ENRUTAMIENTO IP",
        "arp_header": "VECINOS ARP",
        "conns_header": "CONEXIONES TCP/UDP ACTIVAS",
        "ping_header": "COMPROBACIÓN DE ALCANCE",
        "default_gw": "Puerta de enlace predeterminada",
        "hostname": "Nombre del host",
        "os_info": "Sistema operativo",
        "log_saved": "Registro completo guardado en archivo:",
        "not_found": "Registro no encontrado",
        "total_logs": "Registros totales",
        "exit": "Saliendo. ¡Adiós!",
        "up": "ACTIVA", "down": "INACTIVA",
        "filter_on": "Filtro IP activo",
        "filter_off": "Filtro IP desactivado — mostrando todos los registros",
        "filter_bad": "IP/red inválida. Ejemplo: /setip 192.168.1.7 o /setip 192.168.1.0/24",
        "updtime_set": "Intervalo de actualización ajustado a",
        "updtime_bad": "Uso: /updtime <segundos>  (mín 0.5s). Ejemplo: /updtime 5",
        "skipped": "Registro omitido (no coincide con el filtro IP)",
        "wifi_header": "CONEXIÓN WI-FI",
        "bw_header": "ANCHO DE BANDA (RX/TX)",
        "ports_header": "AUDITORÍA DE PUERTOS EN ESCUCHA",
        "dnswatch_header": "VIGILANCIA DE ORIGEN DNS",
        "vpn_header": "VPN / TRÁFICO OCULTO",
        "fp_header": "HUELLA DE SO DEL DISPOSITIVO",
        "anom_header": "COMPROBACIÓN DE ANOMALÍAS",
        "base_header": "COMPARACIÓN CON LÍNEA BASE",
        "stats_header": "ESTADÍSTICAS DE SESIÓN",
        "search_found": "Resultados de búsqueda",
        "search_none": "Ningún registro coincide",
        "detail_header": "CAMPOS DETALLADOS",
        "df_dns": "DNS",
        "df_vpn": "VPN",
        "df_device": "DISPOSITIVO DE ORIGEN",
        "df_os": "SO",
        "sec": "segundo(s)",
        "categories": {
            "success": "ÉXITO", "warning": "SOSPECHOSO", "error": "BLOQUEADO/FALLIDO",
            "masked": "ENMASCARADO", "own": "RED PROPIA",
        },
        "banner_commands": [
            ("/updtime [seg]",   "intervalo de refresco (por defecto 1s)"),
            ("/setip [ip|cidr]", "filtrar por IP o red ('off' para limpiar)"),
            ("scan",             "capturar una nueva instantánea ahora"),
            ("list",             "lista numerada de todos los registros"),
            ("N open-list",      "abrir el registro COMPLETO número N"),
            ("stats",            "estadísticas de sesión por color"),
            ("export [json|csv|html]", "exportar registros a archivo"),
            ("search <texto>",   "buscar registros con texto/regex"),
            ("config",           "ver/guardar config.json persistente"),
            ("version",          "versión + algoritmo de actualización"),
            ("clear",            "limpiar el historial en memoria"),
            ("banner",           "mostrar esta ventana otra vez"),
            ("quit",             "salir"),
        ],
    },
}

LANG = detect_lang()
TR = T[LANG]


def set_lang(lang):
    """Switch active language at runtime (falls back to English)."""
    global LANG, TR
    LANG = lang if lang in SUPPORTED else "en"
    TR = T[LANG]
    return TR
