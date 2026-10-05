# 👁️ Eyes of the Network

> [EN](README.md) · **ES**

[![Versión](https://img.shields.io/badge/versi%C3%B3n-1.2.0-blue)](#-algoritmo-de-actualización)
[![Plataforma](https://img.shields.io/badge/plataforma-Linux-FCC624?logo=linux&logoColor=black)]()
[![Python](https://img.shields.io/badge/python-3.6+-3776AB?logo=python&logoColor=white)]()
[![Licencia](https://img.shields.io/badge/licencia-MIT-green)](LICENSE)
[![Idiomas](https://img.shields.io/badge/idiomas-EN%20|%20ES-lightgrey)]()

**Eyes of the Network** es un monitor de red ligero para terminal en **Linux**.
Captura toda la información de la red a la que está conectado tu dispositivo —
interfaces, direcciones IP/MAC, DNS, tabla de enrutamiento, vecinos ARP, conexiones
TCP/UDP activas y comprobaciones de alcance — y guarda cada instantánea como un
**registro detallado numerado** directamente en tu terminal (y en un archivo).
¿Necesitas releer una captura anterior? Solo escribe su número: `42 open-list`. 🎯

---

## 📑 Índice
- [Características ✨](#-características)
- [Requisitos 📦](#-requisitos)
- [Inicio rápido 🚀](#-inicio-rápido)
- [Comandos 🖥️](#-comandos)
- [Ejemplo de salida 🧾](#-ejemplo-de-salida)
- [Idiomas 🌐](#-idiomas)
- [Algoritmo de actualización 🔢](#-algoritmo-de-actualización)
- [FAQ ❓](#-faq)
- [Seguridad y ética 🔐](#-seguridad-y-ética)
- [Licencia 📄](#-licencia)

---

## Características ✨

- 🌐 **Instantánea completa de red**: interfaces (`/sys/class/net`), IP/MAC, estado del enlace
- 🧬 **Configuración DNS** desde `/etc/resolv.conf`
- 🛣️ **Tabla de enrutamiento** + detección de puerta de enlace predeterminada
- 👥 **Vecinos ARP** — quién más está en tu LAN
- 🔌 **Conexiones TCP/UDP activas** (`ss` / `netstat`)
- 🏓 **Comprobación de alcance** — ping a la puerta de enlace y DNS externo con estadísticas RTT
- 🔢 **Registros numerados** impresos en detalle directamente en el terminal
- 📂 Cada registro también se guarda en `logs/session.log` (a prueba de pérdidas del búfer)
- 🖼️ **Ventana de comandos** — un panel elegante con marco que muestra todos los comandos al iniciar
- ⏱️ **Actualizaciones en vivo** — los registros se refrescan automáticamente **cada segundo** por defecto; cámbialo con `/updtime [seg]`
- 🎨 **Registros por colores**: 🟢 éxito · 🟡 sospechoso · 🔴 bloqueado/fallido · 🟠 enmascarado · 🟣 tu propia red
- 📌 **Filtro IP** — `/setip 192.168.1.0/24` mantiene solo los registros que coinciden con una IP o red (`/setip off` lo desactiva)
- 🔎 `N open-list` — reabre al instante el **registro mega-detallado completo #N**
- 🌍 Interfaz bilingüe: **English** y **Español**

## Requisitos 📦

| Componente | Versión | Notas |
|---|---|---|
| Linux | cualquier distro | Debian/Ubuntu, Fedora, Arch, Alpine... |
| Python | 3.6+ | solo biblioteca estándar — sin instalaciones de pip |
| iproute2 | cualquiera | `ip`, `ss` (normalmente preinstalados) |
| iputils | cualquiera | `ping` |

## Inicio rápido 🚀

```bash
# 1. Clona o descarga el repositorio
git clone https://github.com/WFStudio-app/Eyes-of-the-Network.git
cd Eyes-of-the-Network

# 2. Ejecútalo (español):
python3 net_monitor.py --lang es

# Versión en inglés:
python3 net_monitor.py
```

Al iniciar aparece una **ventana de comandos con marco** que lista todas las órdenes;
luego el monitor captura el **registro #1** y sigue refrescando los registros **cada
segundo** automáticamente. Usa `/updtime 5` para reducir la frecuencia o
`/setip 192.168.1.0/24` para vigilar solo una red. Escribe comandos en el indicador `>`.

## Comandos 🖥️

| Comando | Descripción |
|---|---|
| `scan` | capturar ahora una nueva instantánea de red |
| `/updtime [seg]` | intervalo de actualización en segundos (por defecto `1`, mínimo `0.5`) |
| `/setip [ip\|cidr]` | filtrar por IP o red, p. ej. `/setip 192.168.1.7` o `/setip 10.0.0.0/8`; `/setip off` desactiva |
| `list` | lista numerada de todos los registros capturados |
| `N open-list` | abrir el **registro detallado completo** número N (p. ej. `3 open-list`) |
| `version` | versión del programa + algoritmo de actualización |
| `clear` | limpiar el historial de registros en memoria |
| `banner` | mostrar la ventana de comandos otra vez |
| `help` | mostrar ayuda |
| `quit` / `Ctrl+C` | salir |

## Ejemplo de salida 🧾

```
===== LOG #1 | 2026-10-05 14:22:31 | [ÉXITO] =====
Eyes of the Network v1.2.0 | lang=es
Sistema operativo: Linux, kernel 6.8.0-45-generic
Nombre del host: thinkpad

### INTERFACES DE RED
[eth0] Estado: ACTIVA | Dirección MAC: 3c:7c:3f:12:aa:01
    Direcciones IP: 192.168.1.42/24 (inet)
[lo] Estado: ACTIVA | Dirección MAC: 00:00:00:00:00:00
    Direcciones IP: 127.0.0.1/8 (inet)

### CONFIGURACIÓN DNS
nameserver 192.168.1.1

### TABLA DE ENRUTAMIENTO IP
default via 192.168.1.1 dev eth0 proto dhcp
192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.42
Puerta de enlace predeterminada: 192.168.1.1

### VECINOS ARP
192.168.1.1 dev eth0 lladdr f4:83:77:11:22:33 REACHABLE

### CONEXIONES TCP/UDP ACTIVAS
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port  Process
ESTAB  0      0      192.168.1.42:44312  140.82.121.4:443   users:(("chrome",pid=2211))

### COMPROBACIÓN DE ALCANCE
ping 192.168.1.1: OK (recibidos=3/3, RTT medio=1.24 ms)
ping 8.8.8.8: OK (recibidos=3/3, RTT medio=9.87 ms)
```
> Cada línea se pinta por categoría: 🟢 funcionamiento/exito · 🟣 red local propia
> · 🟡 entradas sospechosas · 🟠 MACs enmascaradas/privadas · 🔴 comprobaciones fallidas o bloqueadas.

## Idiomas 🌐

| Idioma | Cómo activarlo |
|---|---|
| 🇬🇧 English | por defecto / `--lang en` / `LANG_PREFIX=en python3 net_monitor.py` |
| 🇪🇸 Español | `--lang es` / `LANG_PREFIX=es python3 net_monitor.py` |

Documentación disponible en ambos idiomas: [README.md](README.md) (EN) · [README.es.md](README.es.md) (ES)

## Algoritmo de actualización 🔢

Las versiones siguen el formato **`X.X.X` (MAYOR.MENOR.PARCHE)**:

| Versión | Tipo | Significado |
|---|---|---|
| `X.0.0` | 🌋 **Actualización global** | reescritura mayor, cambios incompatibles |
| `0.X.0` | 🚀 **Actualización grande** | nuevas funciones, compatible hacia atrás |
| `0.0.X` | 🔧 **Mini actualización** | correcciones, mejoras pequeñas |

Ejemplo de flujo: `1.0.0 → 1.0.1` (corrección) `→ 1.1.0` (nueva función) `→ 2.0.0` (reescritura global).
Versión actual: **1.2.0** — consulta la [página de lanzamientos](../../releases).

## FAQ ❓

**¿Dónde se guardan los registros?** En memoria (para `open-list`) y en `logs/session.log` (permanente).
Los registros nunca se suben a git (ver `.gitignore`).

**¿Necesito root?** No. Algunos campos (nombres de proceso en `ss -p`) pueden estar ocultos sin root.

**¿Por qué la sección ARP dice "unavailable"?** El contenedor/VM puede carecer de `ip neigh` o de una LAN real. En un host Linux normal funciona sin configuración adicional.

**¿Cómo detengo las actualizaciones en vivo?** Escribe `quit` (detiene el subproceso de registro limpiamente).

**¿Puedo desactivar los colores?** Sí — ejecuta sin TTY o exporta `NO_COLOR=1`.

## Seguridad y ética 🔐

Esta herramienta solo lee información que tu propio sistema operativo ya expone
localmente. Realiza monitoreo pasivo (sin escaneo de puertos, sin inyección de
paquetes). Úsala solo en redes que te pertenezcan o que tengas permiso de monitorear.


## 📂 Estructura del proyecto

```
Eyes-of-the-Network/
├── net_monitor.py            # punto de entrada (REPL + hilo en vivo)
├── eyes/
│   ├── core/                 # version.py · i18n.py · colors.py · logstore.py
│   ├── utils/                # classify.py · banner.py · shell.py
│   └── modules/              # collectors.py · pinger.py · snapshot.py
├── docs/ARCHITECTURE.md      # guía completa de arquitectura
├── scripts/run.sh            # inicio rápido
├── examples/                 # session.log de ejemplo
└── logs/                     # registros (ignorados por git)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## Licencia 📄

[MIT](LICENSE) © 2026 WFStudio-app


## 🔎 Campos detallados (v1.4.0)

Cada registro completo (`N open-list`) empieza con el bloque **CAMPOS DETALLADOS**:

| Campo | Significado |
|---|---|
| `DNS:` | desde qué servidor DNS llegan las respuestas (stub local ⇒ posible ocultación DoH/DoT) |
| `VPN?:` | ¿tráfico oculto tras un túnel? (tun/tap/wg/ppp, puertos VPN, ruta por defecto vía túnel) |
| `DISPOSITIVO DE ORIGEN:` | dispositivo que emitió la señal — MAC + fabricante OUI y **detección de controladores** (Flipper Zero, HackRF, WiFi Pineapple, ESP32/Marauder, Rubber Ducky…) |
| `SO?:` | sistema operativo del origen si está disponible (kernel local + huella TTL de la puerta de enlace) |

## 📦 Nuevos módulos (v1.4.0)

Nuevos comandos: `stats` · `export json|csv|html` · `search <texto|regex>` · `config`
Capas nuevas: `eyes/analysis/` (fingerprint, anomalías, línea base) y `eyes/output/` (exportadores, estadísticas, rotación), además de `wifi`, `bandwidth`, `ports`, `dns_watch`, `vpn`, `device` en `eyes/modules/` y `config`/`search` en `eyes/utils/`.
