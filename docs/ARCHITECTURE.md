# Architecture — Eyes of the Network

Project layout: every function lives in its own file, grouped by folders.

```
Eyes-of-the-Network/
├── net_monitor.py            # entry point (REPL + live thread)
├── eyes/                     # main package
│   ├── core/                 # foundation layer
│   │   ├── version.py        #   X.X.X update algorithm + bump()
│   │   ├── i18n.py           #   EN / ES translations, detect_lang()
│   │   ├── colors.py         #   ANSI colors, category legend, NO_COLOR
│   │   └── logstore.py       #   numbered thread-safe log storage + file
│   ├── utils/                # helpers layer
│   │   ├── classify.py       #   log classification & IP filter (/setip)
│   │   ├── banner.py         #   startup command window (ASCII box)
│   │   └── shell.py          #   safe subprocess runner
│   └── modules/              # data collectors layer
│       ├── collectors.py     #   interfaces / DNS / routes / ARP / connections
│       ├── pinger.py         #   reachability checks
│       └── snapshot.py       #   assembles one full numbered log
├── docs/                     # this architecture doc, guides
├── scripts/                  # helper scripts (run.sh etc.)
├── examples/                 # sample session.log outputs
└── logs/                     # runtime logs (git-ignored)
```

## Layer rules

* `core` imports nothing from `utils`/`modules`.
* `utils` may import `core`.
* `modules` may import `core` + `utils.shell`.
* `net_monitor.py` wires everything together (CLI loop, live thread).

## Log categories (color code)

| Category | Color  | Meaning                                  |
|----------|--------|------------------------------------------|
| success  | GREEN  | normal, working logs                     |
| warning  | YELLOW | suspicious activity                      |
| error    | RED    | blocked / failed / unreachable           |
| masked   | ORANGE | private MAC, hidden/proxied traffic      |
| own      | PURPLE | your own network (local / loopback)      |

## Versioning (X.X.X)

| Bump    | Command kind | Meaning                            |
|---------|--------------|------------------------------------|
| `X.0.0` | global       | breaking rewrite                   |
| `0.X.0` | major        | new features, backward compatible  |
| `0.0.X` | mini         | fixes and tweaks                   |

Use `eyes.core.version.bump("major")` to compute the next release number.

## Adding a new module

1. Create `eyes/modules/<name>.py` returning plain text.
2. Call it from `snapshot.build_full_log()`.
3. If it emits new signals, extend regexes in `utils/classify.py`.
4. Register any new user command in `i18n.TR[*]["banner_commands"]` and
   the REPL in `net_monitor.py`.
