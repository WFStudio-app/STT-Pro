# Changelog — ServerCloud

Versioning scheme: `X.X.X`
- **X.0.0** — Global update (major rewrite, breaking changes)
- **0.X.0** — Major update (new features, backward compatible)
- **0.0.X** — Mini update (fixes, small improvements)

## [1.6.3] — 2026-10-07 — 🔧 Mini update (rename to ServerCloud)
### Changed
- **Project renamed** from "Eyes of the Network" to **ServerCloud** (server-oriented tool):
  repo, README headers, banners, i18n strings, docs, examples and tests updated
### Fixed
- Log header line `===== LOG #N ... =====` was self-classified as ERROR when a
  previous category was written into it — headers are now neutral in classify

## [1.6.2] — 2026-10-06 — 🔧 Mini update (new log format & /linfo)
### Added
- **New list format** for `list`: `[№] (name) (address) (type) (memory MB)` per entry
- **`/linfo [N]`** — opens the full info of one log: metadata header + entire colored body

## [1.6.0] — 2026-10-06 — 🚀 Major update (modes, AI log chat, log trimming)
### Added
- **Startup mode selection window** — pretty boxed dialog: `1 - Personal use` or `2 - Server`; choice saved to config.json (`"mode"`)
- **SERVER mode extras** (`eyes/server/ai_chat.py`):
  - `/ai_api <API-key-or-url>` — connect any OpenAI-compatible neural-network API (bare key, `KEY@URL`, or keyless local URL like Ollama/llama.cpp); stored hidden in config.json
  - `ask <question>` — the AI receives the **last 50 logs** as context and answers; Q/A stored as a numbered log entry
- **`/logd [N]`** — keep only the last N logs in memory (older ones deleted automatically after each new log). Default **50**, `0` = unlimited; persisted in config.json (`logs/session.log` file history is untouched)
- New unit tests for trimming, API parsing, mode window, i18n keys (24 tests total)

## [1.5.0] — 2026-10-06 — 🚀 Major update (new commands)
### Added
- **`back`** — exit full-log view (`N open-list`) and return to the main menu
- **`/onuwifi [path] <ip>`** (`eyes/modules/transmitter.py`) — send a file over the network; writes a transfer summary + numbered log entry with status, size and destination
- **`/cleaner`** (`eyes/modules/cleaner.py`) — completely blocks network file send/receive for 5 seconds; logged as 🔴 blocked event
- **`/blut`** (`eyes/modules/blut.py`) — scan nearby Bluetooth devices; every line prefixed with blue **[B]**
- **`/g`** (`eyes/modules/gscan.py`) — scan surrounding networks and list reachable targets you may send requests to

## [1.5.1] — 2026-10-06 — 🔧 Mini update (bug fixes)
### Fixed
- False `[ERROR]` on interface-state lines like "[lo]/[dummy0] State: DOWN" — neutral down/unavailable patterns now excluded from classification
- Strings "unavailable"/"empty" no longer produce spurious errors in `/blut`, `/g`, wifi scans
- Spanish log line "INACTIVA" covered by the same neutral-down rule
- Regression tests added: 19 unittest tests total (`tests/test_bugs.py`), all passing

## [1.4.1] — 2026-10-06 — 🔧 Mini update (bug fixes)
### Fixed
- **Log misclassification**: banner text "(Ctrl+C to stop logging thread)" matched the `controller` warning pattern, and "State: DOWN" matched bare `down` → every log was labelled `[ERROR]`. Neutral headers now return no category; `down` only counts as error in interface-state lines.
- **"VPN: NO" / "No VPN … found" classified as MASKED** — explicit all-clear statements are now success/neutral.
- **`/setip off` persisted `"off"` into config.json** instead of clearing the filter on next start.
- **Piped stdin (scripts/tests)**: live thread spun unthrottled; live updates now run only in an interactive TTY (`scan` still works when piped).
- Added regression test suite `tests/test_bugs.py` (13 tests, stdlib unittest): classification, filter parsing, exporters on empty/fresh stores, end-to-end REPL runs in EN & ES.

## [1.4.0] — 2026-10-06 — 🚀 Major update
### Added
- **Wi-Fi module** (`eyes/modules/wifi.py`): SSID, BSSID, channel/frequency, RSSI, 802.11 standard
- **Bandwidth module** (`eyes/modules/bandwidth.py`): live RX/TX speed per interface from `/proc/net/dev`, high-traffic alerts
- **Ports audit** (`eyes/modules/ports.py`): listening sockets parsed from `/proc/net/{tcp,udp}`, 0.0.0.0-binding warnings
- **DNS source watch** (`eyes/modules/dns_watch.py`): queries each configured resolver directly — shows *which server* answers and flags local stubs (DoH/DoT masking)
- **VPN / hidden-traffic detector** (`eyes/modules/vpn.py`): tunnel interfaces, VPN default-route, known VPN ports → orange MASKED logs
- **Device analysis** (`eyes/modules/device.py`): MAC OUI vendor lookup, controller-board signatures (Flipper Zero, HackRF, Pineapple, ESP32/Marauder, Rubber Ducky…), TTL→OS heuristics
- **DETAIL FIELDS block** in every full log (`N open-list`): `DNS:` (source server) · `VPN?:` (hidden traffic) · `SOURCE DEVICE:` (who sent the signal + controller check) · `OS?:` (origin OS if available)
- **Analysis layer** (`eyes/analysis/`): fingerprint.py (neighbor OS), anomalies.py (port-scan/flood heuristics), baseline.py (learned network profile, ARP-spoof drift alerts)
- **Output layer** (`eyes/output/`): exporter.py (JSON/CSV/HTML reports), stats.py (session statistics command), rotate.py (log rotation 2MB×3)
- **Persistent config** (`eyes/utils/config.py` + `config.json`): language, interval, IP filter saved automatically
- **Search** (`eyes/utils/search.py`): `search <text|regex>` over all stored logs
- New commands: `stats`, `export json|csv|html`, `search`, `config`
- Classifier extended: new yellow/red/orange triggers for Wi-Fi, VPN, anomaly, port-audit findings

## [1.3.0] — Modular architecture: code split into eyes/core, eyes/utils, eyes/modules
## [1.2.1] — Fixes: log classification (neutral headers), FORCE_COLOR support
## [1.2.0] — Startup command window, live updates (/updtime), IP filter (/setip), color-coded categories
## [1.1.0] — Port to Linux, EN/ES i18n, SemVer update algorithm X.X.X
## [1.0.0] — Initial release: numbered detailed logs, `N open-list`

## [2.0.0] — Global update 🌋 ServerCloud (STT-Pro + TokenPFS merged)

**Renamed & merged:** STT Pro and TokenPFS are now ONE program — **ServerCloud**, industrial software for servers from small to huge.

### Operation modes (startup window or `/mode`)
1. **Personal** — single device / home network monitoring
2. **Server** — datacenter/VPS monitoring + AI log analyst (`/ai_api`, `ask`), auto-clean defaults
3. **AI Factory** — local LLM token generation on any hardware (Ollama engine): 71-model catalog, `/bmc` giants 25 GB+, chat with context `/w`, `/stf`, `/autt`, `/dnm`, `/dnmf`, `/delm`
4. **Full** — all modules at once (network monitor + AI factory)

### New commands
- `/mode [personal|server|ai|full]` — show/switch operation mode live
- `/aimode` — enter the embedded AI Factory; `back` returns to the main menu
- CLI: `python3 net_monitor.py -m full`
- AI extras (`/ai_api`, `ask`) now available in both Server and Full modes

### Cross-platform
- Log header OS line uses `platform.system()` (Linux/macOS/Windows) instead of hardcoded "Linux"

