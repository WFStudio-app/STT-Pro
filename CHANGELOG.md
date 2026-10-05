# Changelog — Eyes of the Network

Versioning scheme: `X.X.X`
- **X.0.0** — Global update (major rewrite, breaking changes)
- **0.X.0** — Major update (new features, backward compatible)
- **0.0.X** — Mini update (fixes, small improvements)

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
