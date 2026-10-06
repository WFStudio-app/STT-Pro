# 👁️ Eyes of the Network

> **EN** · [ES](README.es.md)

[![Version](https://img.shields.io/badge/version-1.2.0-blue)](#-update-algorithm)
[![Platform](https://img.shields.io/badge/platform-Linux-FCC624?logo=linux&logoColor=black)]()
[![Python](https://img.shields.io/badge/python-3.6+-3776AB?logo=python&logoColor=white)]()
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Langs](https://img.shields.io/badge/languages-EN%20|%20ES-lightgrey)]()

**Eyes of the Network** is a lightweight terminal network monitor for **Linux**.
It captures everything about the network your device is connected to — interfaces,
IP/MAC addresses, DNS, routing table, ARP neighbors, active TCP/UDP connections and
reachability checks — and stores every snapshot as a **numbered detailed log** right
in your terminal (and in a file). Need to re-read an old snapshot? Just type its
number: `42 open-list`. 🎯

---

## 📑 Table of contents
- [Features ✨](#-features)
- [Requirements 📦](#-requirements)
- [Quick start 🚀](#-quick-start)
- [Commands 🖥️](#-commands)
- [Example output 🧾](#-example-output)
- [Languages 🌐](#-languages)
- [Update algorithm 🔢](#-update-algorithm)
- [FAQ ❓](#-faq)
- [Security & ethics 🔐](#-security--ethics)
- [License 📄](#-license)

---

## Features ✨

- 🌐 **Full network snapshot**: interfaces (`/sys/class/net`), IP/MAC, link state
- 🧬 **DNS config** from `/etc/resolv.conf`
- 🛣️ **Routing table** + default gateway detection
- 👥 **ARP neighbors** — who else is on your LAN
- 🔌 **Active TCP/UDP connections** (`ss` / `netstat`)
- 🏓 **Reachability check** — ping to gateway and external DNS with RTT stats
- 🔢 **Numbered logs** printed in detail straight to the terminal
- 📂 Every log also persisted to `logs/session.log` (survives scrollback loss)
- 🖼️ **Command window banner** — a beautiful framed panel with all commands shown on startup
- ⏱️ **Live updates** — logs refresh automatically **every second** by default; change it with `/updtime [sec]`
- 🎨 **Color-coded logs**: 🟢 success · 🟡 suspicious · 🔴 blocked/failed · 🟠 masked · 🟣 your own network
- 📌 **IP filter** — `/setip 192.168.1.0/24` keeps only logs that match an IP or network (`/setip off` clears)
- 🔎 `N open-list` — instantly reopen the **full mega-detailed log #N**
- 🌍 Bilingual UI: **English** and **Español**

## Requirements 📦

| Component | Version | Notes |
|---|---|---|
| Linux | any distro | Debian/Ubuntu, Fedora, Arch, Alpine... |
| Python | 3.6+ | standard library only — no pip installs needed |
| iproute2 | any | `ip`, `ss` (usually preinstalled) |
| iputils | any | `ping` |

## Quick start 🚀

```bash
# 1. Clone or download the repo
git clone https://github.com/WFStudio-app/Eyes-of-the-Network.git
cd Eyes-of-the-Network

# 2. Run it (English by default)
python3 net_monitor.py

# Spanish version:
python3 net_monitor.py --lang es
```

On startup a **framed command window** appears listing every command, then the monitor
captures **log #1** and keeps refreshing the logs **every second** automatically.
Use `/updtime 5` to slow it down, `/setip 192.168.1.0/24` to watch only one network.
Type commands at the `>` prompt.

## Commands 🖥️

| Command | Description |
|---|---|
| `scan` | capture a new network snapshot now |
| `/updtime [sec]` | set the live log update interval in seconds (default `1`, min `0.5`) |
| `/setip [ip\|cidr]` | filter logs by IP or network, e.g. `/setip 192.168.1.7` or `/setip 10.0.0.0/8`; `/setip off` disables |
| `list` | numbered list of all captured logs |
| `N open-list` | open the **full detailed log** number N (e.g. `3 open-list`) |
| `back` | return from log-reading view to the main menu / command window |
| `/onuwifi [path] <ip>` | send a file over the network + transfer summary log |
| `/cleaner` | block network file send/receive for 5 seconds (logged as BLOCKED) |
| `/blut` | scan nearby Bluetooth devices — every line prefixed blue `[B]` |
| `/g` | scan surrounding networks & list reachable targets for requests |
| `stats` | session statistics per log color |
| `export [json\|csv\|html]` | export all logs to a report file |
| `search <text\|regex>` | find logs containing text/regex |
| `config` | show/save persistent config.json |
| `version` | program version + update algorithm |
| `clear` | clear log history in memory |
| `banner` | show the command window again |
| `help` | show help |
| `quit` / `Ctrl+C` | exit |

## Example output 🧾

```
===== LOG #1 | 2026-10-05 14:22:31 | [SUCCESS] =====
Eyes of the Network v1.2.0 | lang=en
Operating system: Linux, kernel 6.8.0-45-generic
Hostname: thinkpad

### NETWORK INTERFACES
[eth0] State: UP | MAC address: 3c:7c:3f:12:aa:01
    IP addresses: 192.168.1.42/24 (inet)
[lo] State: UP | MAC address: 00:00:00:00:00:00
    IP addresses: 127.0.0.1/8 (inet)

### DNS CONFIGURATION
nameserver 192.168.1.1

### IP ROUTING TABLE
default via 192.168.1.1 dev eth0 proto dhcp
192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.42
Default gateway: 192.168.1.1

### ARP NEIGHBORS
192.168.1.1 dev eth0 lladdr f4:83:77:11:22:33 REACHABLE

### ACTIVE TCP/UDP CONNECTIONS
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port  Process
ESTAB  0      0      192.168.1.42:44312  140.82.121.4:443   users:(("chrome",pid=2211))

### REACHABILITY CHECK
ping 192.168.1.1: OK (received=3/3, avg RTT=1.24 ms)
ping 8.8.8.8: OK (received=3/3, avg RTT=9.87 ms)
```
> Each line is painted by category: 🟢 working/success · 🟣 your local network
> · 🟡 suspicious entries · 🟠 masked/private MACs · 🔴 failed or blocked checks.

## Languages 🌐

| Language | How to enable |
|---|---|
| 🇬🇧 English | default / `--lang en` / `LANG_PREFIX=en python3 net_monitor.py` |
| 🇪🇸 Español | `--lang es` / `LANG_PREFIX=es python3 net_monitor.py` |

Docs are available in both languages: [README.md](README.md) (EN) · [README.es.md](README.es.md) (ES)

## Update algorithm 🔢

Versions follow the format **`X.X.X` (MAJOR.MINOR.PATCH)**:

| Version | Type | Meaning |
|---|---|---|
| `X.0.0` | 🌋 **Global update** | major rewrite, breaking changes |
| `0.X.0` | 🚀 **Major update** | new features, backward compatible |
| `0.0.X` | 🔧 **Mini update** | bug fixes, small improvements |

Example flow: `1.0.0 → 1.0.1` (fix) `→ 1.1.0` (new feature) `→ 2.0.0` (global rewrite).
Current version: **1.2.0** — see the [releases page](../../releases).

## FAQ ❓

**Where are logs stored?** In memory (for `open-list`) and in `logs/session.log` (permanent).
Logs are never committed to git (see `.gitignore`).

**Do I need root?** No. Some fields (process names in `ss -p`) may be hidden without root.

**Why does the ARP section say "unavailable"?** The container/VM may lack `ip neigh` or a real LAN. On a normal Linux host it works out of the box.

**How do I stop the live updates?** Type `quit` (stops the logging thread cleanly).

**Can I disable colors?** Yes — run without a TTY or export `NO_COLOR=1`.

## Security & ethics 🔐

This tool only reads information your own OS already exposes locally. It performs
passive monitoring (no port scanning, no packet injection). Use it only on networks
you own or have permission to monitor.


## 📂 Project structure

```
Eyes-of-the-Network/
├── net_monitor.py            # entry point (REPL + live thread)
├── eyes/
│   ├── core/                 # version.py · i18n.py · colors.py · logstore.py
│   ├── utils/                # classify.py · banner.py · shell.py
│   └── modules/              # collectors.py · pinger.py · snapshot.py
├── docs/ARCHITECTURE.md      # full architecture guide
├── scripts/run.sh            # quick start
├── examples/                 # sample session.log
└── logs/                     # runtime logs (git-ignored)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## License 📄

[MIT](LICENSE) © 2026 WFStudio-app


## 🔎 Detailed Fields (v1.4.0)

Every full log (`N open-list`) starts with a **DETAIL FIELDS** block:

| Field | Meaning |
|---|---|
| `DNS:` | which DNS server the answers come from (local stub ⇒ possible DoH/DoT masking) |
| `VPN?:` | is traffic hidden behind a tunnel (tun/tap/wg/ppp, VPN ports, default route via tunnel) |
| `SOURCE DEVICE:` | device that emitted the signal — MAC + OUI vendor, plus **controller-board detection** (Flipper Zero, HackRF, WiFi Pineapple, ESP32/Marauder, Rubber Ducky…) |
| `OS?:` | operating system of the origin if available (local kernel + TTL fingerprint of the gateway) |

## 📦 New Modules (v1.4.0)

```
eyes/modules/   wifi.py        SSID / BSSID / channel / RSSI / 802.11 standard
                bandwidth.py   live RX/TX speed per interface
                ports.py       listening-socket audit (/proc/net)
                dns_watch.py   direct probe of every configured resolver
                vpn.py         tunnel & hidden-traffic detector
                device.py      OUI vendors, controller signatures, TTL→OS
eyes/analysis/  fingerprint.py neighbor OS guesses
                anomalies.py   port-scan / connection-flood heuristics
                baseline.py    learned network profile, ARP-spoof drift alerts
eyes/output/    exporter.py    JSON / CSV / HTML reports
                stats.py       session statistics per log color
                rotate.py      log rotation (2 MB × 3 files)
eyes/utils/     config.py      persistent config.json
                search.py      regex search over all logs
```

New commands: `stats` · `export json|csv|html` · `search <text|regex>` · `config`
