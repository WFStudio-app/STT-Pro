"""Regression tests for v1.4.1 bug fixes (run: python3 -m pytest tests/ -v).

Bugs covered:
  B1  classify_line("(Ctrl+C to stop logging thread)") must NOT be a warning
      (substring 'control' matched the 'controller' pattern) -> every log was
      mislabelled [ERROR]/[WARNING].
  B2  bare word "down" ("State: DOWN") must not match error unless it is an
      interface state; "[lo] State: DOWN" may be error, but banner text no.
  B3  categorize_full of a clean snapshot must be 'success', not forced by
      neutral header lines.
  B4  /setip 'off' handling in REPL persists "" (not "off") into config.json.
  B5  search/export/stats/listing work on a fresh LogStore without crashing.
  B6  parse_filter rejects garbage, accepts ip/cidr/off.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eyes.core.logstore import LogStore                    # noqa: E402
from eyes.utils.classify import (classify_line,            # noqa: E402
                                 categorize_full, parse_filter,
                                 IP_FILTER)
from eyes.output.exporter import export_csv, export_html, export_json  # noqa: E402
from eyes.output.stats import session_stats                # noqa: E402
from eyes.utils.search import search_logs                  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestClassify(unittest.TestCase):
    def test_b1_ctrl_c_not_controller(self):
        self.assertIsNone(classify_line("Monitor iniciado — actualizaciones cada 5.0s."
                                        "  (Ctrl+C to stop logging thread)"))

    def test_b1_banner_headers_neutral(self):
        self.assertIsNone(classify_line(
            "ServerCloud — Linux network monitor v1.4.1 | lang=en"))
        self.assertIsNone(classify_line("Operating system: Linux, kernel 4.19"))
        self.assertIsNone(classify_line("Hostname: myhost"))
        self.assertIsNone(classify_line("### DETAIL FIELDS"))

    def test_b2_state_down_is_error(self):
        self.assertEqual(classify_line("[eth0] State: DOWN | MAC address: x"),
                         "error")

    def test_b2_plain_word_down_ok(self):
        self.assertIsNone(classify_line("Traffic went down overnight"))

    def test_real_signals_still_work(self):
        self.assertEqual(classify_line("ping 1.2.3.4: timeout"), "error")
        self.assertEqual(classify_line("DNS over HTTPS detected (DoH)"),
                         "masked")
        self.assertEqual(classify_line("possible arp spoof attack"), "warning")
        self.assertEqual(classify_line("Flipper Zero controller board seen"),
                         "warning")
        self.assertEqual(classify_line("peer 192.168.1.55 established"),
                         "own")

    def test_b3_clean_snapshot_success(self):
        text = "\n".join([
            "ServerCloud — Linux network monitor v1.4.1 | lang=en",
            "Operating system: Linux, kernel 4.19",
            "### NETWORK INTERFACES",
            "[eth0] State: UP | MAC address: aa:bb:cc:dd:ee:ff",
            "nameserver 1.1.1.1",
        ])
        self.assertEqual(categorize_full(text), "success")

    def test_b3_severity_wins(self):
        text = "header line\n[eth0] State: DOWN\nsome ok line"
        self.assertEqual(categorize_full(text), "error")

    def test_b6_parse_filter(self):
        self.assertTrue(parse_filter("192.168.1.0/24"))
        self.assertTrue(parse_filter("10.0.0.5"))
        self.assertTrue(parse_filter("off"))
        self.assertFalse(IP_FILTER["nets"])
        self.assertFalse(parse_filter("garbage!!"))


class TestOutputs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.store = LogStore(log_dir=self.tmp,
                              log_file=os.path.join(self.tmp, "session.log"))
        self.store.add("log one\n[eth0] State: UP", "success")
        self.store.add("log two\nping failed", "error")

    def test_b5_listing_search_stats_export(self):
        self.assertIn("[1] (log one)", self.store.listing())
        self.assertIn("[2] (log two)", self.store.listing())
        out = search_logs(self.store, "failed")
        self.assertIn("#2", out)
        stats = session_stats(self.store)
        self.assertIn("2", stats)
        p = export_json(self.store, os.path.join(self.tmp, "r.json"))
        with open(p) as f:
            data = json.load(f)
        self.assertEqual(len(data["logs"]), 2)
        export_csv(self.store, os.path.join(self.tmp, "r.csv"))
        html_p = export_html(self.store, os.path.join(self.tmp, "r.html"))
        with open(html_p) as f:
            self.assertIn("#1", f.read())

    def test_empty_store_no_crash(self):
        s = LogStore(log_dir=self.tmp, log_file=os.path.join(self.tmp, "e.log"))
        self.assertIn("0", s.listing())
        search_logs(s, "anything")
        session_stats(s)
        export_json(s, os.path.join(self.tmp, "e.json"))


class TestRepl(unittest.TestCase):
    """End-to-end REPL run through a pipe (also covers piped-stdin hang fix)."""

    def _run(self, cmds, lang=None):
        args = [sys.executable, os.path.join(ROOT, "net_monitor.py")]
        if lang:
            args += ["--lang", lang]
        return subprocess.run(args, input="\n".join(cmds) + "\n",
                              capture_output=True, text=True, timeout=60,
                              cwd=ROOT)

    def test_b4_setip_off_and_categories(self):
        r = self._run(["/setip 192.168.1.0/24", "/setip off", "scan",
                       "list", "quit"])
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn("IP filter active", out)
        self.assertIn("IP filter disabled", out)
        # the startup log entry must no longer be mislabelled [ERROR]
        # (v1.4.x bug: banner 'Ctrl+C' -> 'controller', VPN:'NO' -> masked)
        self.assertNotIn("[ERROR   ] ServerCloud", out)
        self.assertNotIn("[WARNING ] ServerCloud", out)
        with open(os.path.join(ROOT, "config.json")) as f:
            cfg = json.load(f)
        self.assertEqual(cfg["setip"], "")          # 'off' persisted as ''

    def test_es_smoke(self):
        r = self._run(["scan", "list", "1 open-list", "quit"], lang="es")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("CAMPOS DETALLADOS", r.stdout)

    def test_open_list_colors_and_bad_number(self):
        r = self._run(["scan", "1 open-list", "999 open-list", "quit"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("DETAIL FIELDS", r.stdout)
        self.assertIn("Log not found: #999", r.stdout)


class TestV15Bugs(unittest.TestCase):
    """v1.5.1 fixes — logs about the new commands must be classified right."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _run(self, cmds, lang=None):
        args = [sys.executable, os.path.join(ROOT, "net_monitor.py")]
        if lang:
            args += ["--lang", lang]
        return subprocess.run(args, input="\n".join(cmds) + "\n",
                              capture_output=True, text=True, timeout=120,
                              cwd=self.tmp)

    def test_lo_down_is_neutral(self):
        # v1.5.0 bug: "[lo] State: DOWN" / "[dummy0] State: DOWN" matched the
        # error pattern and forced EVERY snapshot to [ERROR].
        self.assertIsNone(classify_line("[lo] State: DOWN | MAC address: x"))
        self.assertIsNone(classify_line("[dummy0] State: DOWN | MAC: y"))
        self.assertIsNone(classify_line("Estado: INACTIVA"))
        # a real interface going down is still an error
        self.assertEqual(classify_line("[eth0] State: DOWN"), "error")

    def test_unavailable_lines_are_neutral(self):
        # v1.5.0 bug: 'unavailable' in info lines was treated as failure
        self.assertIsNone(classify_line(
            "Wi-Fi information unavailable (no iw / nmcli)"))
        self.assertIsNone(classify_line("(ARP table empty / unavailable)"))
        # genuine failures still red
        self.assertEqual(classify_line(
            "ping 8.8.8.8: FAIL (unreachable / blocked)"), "error")

    def test_send_success_log_not_purple(self):
        # v1.5.0 bug: private/OUI MAC inside the destination path made a
        # successful [SEND] transfer log show up as [OWN] (purple)
        ok, text = None, None
        from eyes.modules.transmitter import send_file
        p = os.path.join(self.tmp, "f.txt")
        with open(p, "w") as f:
            f.write("x" * 100)
        ok, text = send_file(p, "192.0.2.7")       # TEST-NET ip: no listener
        self.assertTrue(ok)
        cat = categorize_full(text)
        self.assertNotEqual(cat, "own")
        self.assertNotEqual(cat, "masked")
        self.assertIn("[SEND]", text)

    def test_bt_error_stays_blue(self):
        # Bluetooth errors keep the blue [B] category (not red)
        self.assertEqual(classify_line(
            "[B] ERROR: no Bluetooth stack found"), "bt")

    def test_new_commands_repl_end_to_end(self):
        # every command must run without crashing AND store its own numbered
        # log (the user-visible proof that the action happened)
        r = self._run(["/onuwifi",                       # usage hint
                       "/blut",                          # bt scan (blue)
                       "/g",                             # network scan
                       "back",                           # back to menu
                       "list", "quit"])
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn("Usage: /onuwifi", out)           # bad-arg message
        self.assertIn("[B] BLUETOOTH SCAN STARTED", out)
        self.assertIn("[G] NETWORK SCAN", out)
        self.assertIn("main menu", out)                 # back -> banner/menu
        # each of /blut and /g produced a stored log number
        self.assertGreaterEqual(out.count("Log stored"), 2)
        # and they appear in the numbered listing
        self.assertIn("#", out)

    def test_onuwifi_bad_path_is_error_red(self):
        r = self._run(["/onuwifi /definitely/not/here 10.0.0.1", "list", "quit"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("file not found", r.stdout)
        self.assertIn("ERROR", r.stdout)               # logged as error entry


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestV160Features(unittest.TestCase):
    """Regression tests for v1.6.0: /logd trimming, mode window, AI api parse."""

    def test_logstore_trim(self):
        from eyes.core.logstore import LogStore
        import tempfile, os
        d = tempfile.mkdtemp()
        s = LogStore(log_dir=d, log_file=os.path.join(d, "x.log"))
        for i in range(10):
            s.add(f"log {i}", "success", max_logs=5)
        self.assertEqual(len(s.entries), 5)
        self.assertEqual(sorted(s.entries), [6, 7, 8, 9, 10])
        # max_logs=0 -> unlimited
        for i in range(10):
            s.add(f"more {i}", "success", max_logs=0)
        self.assertEqual(len(s.entries), 15)  # 5 kept + 10 new (max_logs=0 -> no trim)

    def test_parse_api_variants(self):
        from eyes.server.ai_chat import parse_api
        base, key = parse_api("sk-abc123")
        self.assertEqual(base, "https://api.openai.com/v1")
        self.assertEqual(key, "sk-abc123")
        base, key = parse_api("mykey@http://localhost:11434/v1")
        self.assertEqual(base, "http://localhost:11434")
        self.assertEqual(key, "mykey")
        base, key = parse_api("http://host:8080/v1/chat/completions")
        self.assertEqual(base, "http://host:8080")
        self.assertEqual(key, "")
        self.assertEqual(parse_api(""), (None, None))

    def test_mode_window_both_langs(self):
        from eyes.core import i18n
        for lang in ("en", "es"):
            box, t = i18n.mode_window(lang)
            self.assertIn("1", box)
            self.assertIn("2", box)
            self.assertTrue(t["ask"])

    def test_i18n_new_keys_present(self):
        from eyes.core import i18n
        keys = ("logd_set", "logd_bad", "logd_unlimited", "ai_need_server",
                "ai_api_set", "ai_api_bad", "ask_bad", "ai_thinking",
                "ai_log_head", "logd_logs", "logd_trimmed", "ai_no_key", "ai_api_off")
        for lang in ("en", "es"):
            for k in keys:
                self.assertIn(k, i18n.T[lang], f"{lang}:{k} missing")

    def test_config_defaults_v160(self):
        from eyes.utils import config
        self.assertEqual(config.DEFAULTS["logd"], 50)
        self.assertIn("mode", config.DEFAULTS)
        self.assertIn("ai_api", config.SECRET_KEYS)
