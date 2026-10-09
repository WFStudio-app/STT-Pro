"""Internationalization (English / Spanish) for ServerCloud.

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


# ---------------------------------------------------------------------------
# Startup mode-selection window (personal / server). Language-independent
# labels are translated via TR once a language is chosen; this dict holds
# both languages so the window can be shown before/after language detection.
# ---------------------------------------------------------------------------
MODE_TEXTS = {
    "en": {
        "q_title": "SELECT OPERATION MODE",
        "q_line": "What will ServerCloud be used for?",
        "personal": "1 - Personal       single device / home network monitoring",
        "server":   "2 - Server         datacenter/VPS monitoring + AI log analyst (/ai_api, ask)",
        "ai":       "3 - AI Factory     local LLM token generation on any hardware (Ollama)",
        "full":     "4 - Full           ALL modules: network monitor + AI factory (industrial)",
        "ask":      "Choose [1/2/3/4] (default 1): ",
        "chosen_p": "Mode: PERSONAL — standard monitoring.",
        "chosen_s": ("Mode: SERVER — extra commands enabled: "
                     "/ai_api <API-key-or-url>, ask <question>."),
        "bad": "Invalid choice, using Personal mode.",
    },
    "es": {
        "q_title": "ELIGE EL MODO DE OPERACIÓN",
        "q_line": "¿Para qué se usará ServerCloud?",
        "personal": "1 - Personal       monitoreo de un dispositivo / red doméstica",
        "server":   "2 - Servidor       monitoreo datacenter/VPS + analista IA (/ai_api, ask)",
        "ai":       "3 - Fábrica IA     generación local de LLM en cualquier hardware (Ollama)",
        "full":     "4 - Completo       TODOS los módulos: monitor de red + fábrica IA (industrial)",
        "ask":      "Elige [1/2/3/4] (por defecto 1): ",
        "chosen_p": "Modo: PERSONAL — monitoreo estándar.",
        "chosen_s": ("Modo: SERVIDOR — comandos extra activados: "
                     "/ai_api <clave-o-url>, ask <pregunta>."),
        "bad": "Opción inválida, usando modo Personal.",
    },
}


def mode_window(lang="en"):
    """Return the pretty boxed startup mode-selection text lines."""
    t = MODE_TEXTS.get(lang, MODE_TEXTS["en"])
    width = 66
    lines = ["╔" + "═" * width + "╗",
             "║" + t["q_title"].center(width) + "║",
             "║" + t["q_line"].center(width) + "║",
             "╠" + "═" * width + "╣",
             "║ " + t["personal"].ljust(width - 1) + "║",
             "║ " + t["server"].ljust(width - 1) + "║",
             "║ " + t["ai"].ljust(width - 1) + "║",
             "║ " + t["full"].ljust(width - 1) + "║",
             "╚" + "═" * width + "╝"]
    return "\n".join(lines), t


T = {
    "en": {
        "title": "ServerCloud — Network monitor + AI factory",
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
        "back_ok": "Returned to the main menu.",
        "log_num": "Log stored",
        "onuwifi_bad": "Usage: /onuwifi <path-to-file> [destination-ip]",
        "onuwifi_sending": "sending file:",
        "cleaner_start": "Blocking network file send/receive for 5 seconds...",
        "blut_start": "Scanning nearby Bluetooth devices...",
        "g_start": "Scanning surrounding networks for reachable targets...",
        "g_hint": "listed networks accept requests",
        "logd_set": "Old logs will be deleted after each",
        "logd_logs": "logs",
        "logd_unlimited": "Log trimming disabled — all logs kept in memory",
        "logd_bad": "Usage: /logd <number>  (0 = keep everything). Example: /logd 100",
        "logd_trimmed": "Trimmed oldest logs from memory:",
        "bserver_on": "EXTENDED MODE ON — company / large-network monitoring. Auto-clean set to 250 logs.",
        "bserver_off": "Extended mode OFF — returned to standard monitoring.",
        "bserver_start": "Scanning the whole network (subnets, ARP, hosts)...",
        "bserver_bad": "Usage: /bserver   ('on'/'off' to toggle; no argument = one-time scan)",
        "bserver_active": "Extended mode is ACTIVE (auto-clean 250). Use '/bserver off' to disable.",
        "ai_need_server": "AI chat is only available in SERVER mode (choose it at startup or set \"mode\": \"server\" in config.json).",
        "ai_api_set": "AI API configured. Ask with: ask <question>",
        "ai_api_bad": "Usage: /ai_api <API-key-or-url>   ('off' to clear)",
        "ai_api_off": "AI API key cleared.",
        "ai_no_key": "No API configured yet. Use: /ai_api <API-key-or-url>",
        "ask_bad": "Usage: ask <question about the last 50 logs>",
        "ai_thinking": "Asking the neural network (last 50 logs as context)...",
        "ai_log_head": "AI CHAT",
        "categories": {
            "success": "SUCCESS", "warning": "SUSPICIOUS", "error": "BLOCKED/FAILED",
            "masked": "MASKED", "own": "OWN NETWORK", "bt": "BLUETOOTH",
        },
        "banner_commands": [
            ("/updtime [sec]",   "set log refresh interval (default 1s)"),
            ("/setip [ip|cidr]", "filter logs by IP or network ('off' to clear)"),
            ("scan",             "capture a new snapshot right now"),
            ("list",             "[№] (name) (address) (type) (memory MB) per log"),
            ("N open-list",      "open the FULL detailed log number N"),
            ("/linfo [N]",       "full info of one log: metadata + entire body"),
            ("back",             "return to the main menu / command window"),
            ("/mode [name]",     "show/switch operation mode: personal|server|ai|full"),
            ("/aimode",          "open AI Factory — local LLMs, /w chat, /stf tok/s, /bmc 25GB+"),
            ("/onuwifi [path] <ip>", "send a FILE over the network + transfer log"),
            ("/cleaner",         "block network file send/receive for 5 seconds"),
            ("/blut",            "scan nearby Bluetooth devices ([B] blue logs)"),
            ("/g",               "scan surrounding networks & reachable targets"),
            ("/logd [N]",        "delete oldest logs after every N stored (default 50, 0=off)"),
            ("/bserver [on|off]", "extended mode: monitor the whole company/large network (auto-clean 250)"),
            ("/ai_api [API]",    "SERVER mode: set neural-network API key/url for log chat"),
            ("ask <question>",   "SERVER mode: AI analyzes the last 50 logs and answers"),
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
        "title": "ServerCloud — Monitor de red + fábrica IA",
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
        "back_ok": "Volviste al menú principal.",
        "log_num": "Registro guardado",
        "onuwifi_bad": "Uso: /onuwifi <ruta-del-archivo> [ip-destino]",
        "onuwifi_sending": "enviando archivo:",
        "cleaner_start": "Bloqueando envío/recepción de archivos por 5 segundos...",
        "blut_start": "Escaneando dispositivos Bluetooth cercanos...",
        "g_start": "Escaneando redes cercanas para encontrar destinos disponibles...",
        "g_hint": "las redes listadas aceptan solicitudes",
        "logd_set": "Los registros viejos se borrarán tras cada",
        "logd_logs": "registros",
        "logd_unlimited": "Purga desactivada — todos los registros se conservan",
        "logd_bad": "Uso: /logd <número>  (0 = conservar todo). Ejemplo: /logd 100",
        "logd_trimmed": "Registros antiguos eliminados de memoria:",
        "bserver_on": "MODO EXTENDIDO ACTIVADO — monitoreo de red corporativa/grande. Limpieza automática: 250 registros.",
        "bserver_off": "Modo extendido DESACTIVADO — regreso al monitoreo estándar.",
        "bserver_start": "Escaneando toda la red (subredes, ARP, hosts)...",
        "bserver_bad": "Uso: /bserver   ('on'/'off' para alternar; sin argumento = escaneo único)",
        "bserver_active": "Modo extendido ACTIVO (limpieza 250). Usa '/bserver off' para desactivarlo.",
        "ai_need_server": "El chat con IA solo está disponible en modo SERVIDOR (elígelo al inicio o pon \"mode\": \"server\" en config.json).",
        "ai_api_set": "API de IA configurada. Pregunta con: ask <pregunta>",
        "ai_api_bad": "Uso: /ai_api <clave-o-url-de-API>   ('off' para limpiar)",
        "ai_api_off": "Clave de API eliminada.",
        "ai_no_key": "Aún no hay API configurada. Usa: /ai_api <clave-o-url>",
        "ask_bad": "Uso: ask <pregunta sobre los últimos 50 registros>",
        "ai_thinking": "Consultando a la red neuronal (últimos 50 registros como contexto)...",
        "ai_log_head": "CHAT IA",
        "categories": {
            "success": "ÉXITO", "warning": "SOSPECHOSO", "error": "BLOQUEADO/FALLIDO",
            "masked": "ENMASCARADO", "own": "RED PROPIA", "bt": "BLUETOOTH",
        },
        "banner_commands": [
            ("/updtime [seg]",   "intervalo de refresco (por defecto 1s)"),
            ("/setip [ip|cidr]", "filtrar por IP o red ('off' para limpiar)"),
            ("scan",             "capturar una nueva instantánea ahora"),
            ("list",             "[№] (nombre) (dirección) (tipo) (memoria MB) por registro"),
            ("N open-list",      "abrir el registro COMPLETO número N"),
            ("/linfo [N]",       "info completa de un registro: metadatos + cuerpo entero"),
            ("back",             "volver al menú principal / ventana de comandos"),
            ("/mode [nombre]",   "ver/cambiar modo: personal|server|ai|full"),
            ("/aimode",          "Abrir Fábrica IA — LLM locales, /w chat, /stf tok/s, /bmc 25GB+"),
            ("/onuwifi [ruta] <ip>", "enviar un ARCHIVO por la red + registro"),
            ("/cleaner",         "bloquear envío/recepción de archivos 5 segundos"),
            ("/blut",            "escanear Bluetooth cercano (registros [B] azules)"),
            ("/g",               "escanear redes cercanas y destinos disponibles"),
            ("/logd [N]",        "borrar registros viejos tras cada N guardados (def. 50, 0=no)"),
            ("/bserver [on|off]", "modo extendido: red corporativa/grande (limpieza auto 250)"),
            ("/ai_api [API]",    "modo SERVIDOR: clave/url de la IA para chatear con logs"),
            ("ask <pregunta>",   "modo SERVIDOR: la IA analiza los últimos 50 registros"),
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
