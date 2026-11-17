"""The page-proof skill's capture script, run as a seat runs it, against pages a local server serves."""

import functools
import http.server
import json
import os
import shutil
import signal
import socket
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CAPTURE = REPO / "rigs" / "shipwrights" / "agents" / "shipwrights" / "skills" / "page-proof" / "scripts" / "capture.mjs"

HEAD = '<!doctype html><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{margin:0}</style>'
FITS = HEAD + "<h1>Fits</h1>"
OVERFLOWS = HEAD + '<main><div id="wide" style="width:600px;height:20px;background:red"></div></main>'
# A --start command as an app's would be: the shell runs the server as a child of its own rather than becoming it
# (the leading `sleep 0;` stops it exec-ing a lone command), so stopping it has to reach the whole group.
SERVE = "sleep 0; python3 -m http.server {port} --bind 127.0.0.1 --directory {site}"


def capture(*args, cwd=None):
    return subprocess.run(["node", str(CAPTURE), *args], capture_output=True, text=True, cwd=cwd, timeout=300)


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def listening(port):
    with socket.socket() as probe:
        return probe.connect_ex(("127.0.0.1", port)) == 0


class PageProofTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("node"):
            raise unittest.SkipTest("node isn't installed")
        probe = capture("--probe")
        if probe.returncode != 0:
            if os.environ.get("CI"):
                raise AssertionError(f"page-proof can't start a browser in CI:\n{probe.stderr}")
            raise unittest.SkipTest(f"no browser for page-proof here: {probe.stderr.strip()}")
        cls.site = tempfile.TemporaryDirectory()
        (Path(cls.site.name) / "fits.html").write_text(FITS)
        (Path(cls.site.name) / "overflows.html").write_text(OVERFLOWS)
        handler = functools.partial(QuietHandler, directory=cls.site.name)
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.site.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def report(self, name):
        return {entry["width"]: entry for entry in json.loads((self.out / f"{name}.json").read_text())["widths"]}

    def test_a_page_that_fits_is_kept_at_both_widths_with_its_actual_viewport(self):
        result = capture(f"{self.base}/fits.html", "--name", "home", "--out", str(self.out))
        self.assertEqual(result.returncode, 0, result.stderr)
        for width in (1440, 390):
            self.assertEqual((self.out / f"home-{width}.png").read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        report = self.report("home")
        self.assertEqual(sorted(report), [390, 1440])
        self.assertEqual(report[390]["viewport"]["width"], 390)
        self.assertEqual(report[1440]["viewport"]["width"], 1440)
        self.assertFalse(report[390]["overflow"]["overflows"])
        self.assertIn('--media "home-1440.png,home-390.png"', result.stdout)

    def test_a_page_wider_than_the_phone_exits_1_and_names_where_the_overflow_starts(self):
        result = capture(f"{self.base}/overflows.html", "--name", "wide", "--out", str(self.out))
        self.assertEqual(result.returncode, 1, result.stderr)
        report = self.report("wide")
        self.assertFalse(report[1440]["overflow"]["overflows"])
        phone = report[390]["overflow"]
        self.assertTrue(phone["overflows"])
        self.assertEqual(phone["by"], 210)
        self.assertEqual([o["element"] for o in phone["offenders"]], ["div#wide"])
        # A phone zooms out to show the whole wider page, so the viewport it actually got is the page's width.
        self.assertEqual(report[390]["viewport"]["width"], 600)
        self.assertIn("(asked for 390), overflows by 210 px: div#wide -> wide-390.png", result.stdout)

    def test_start_runs_the_server_on_the_port_it_names_and_always_stops_it(self):
        port = free_port()
        serve = SERVE.replace("{site}", self.site.name)
        result = capture("http://127.0.0.1:{port}/fits.html", "--start", serve, "--port", str(port),
                         "--out", str(self.out))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads((self.out / "page.json").read_text())["url"], f"http://127.0.0.1:{port}/fits.html")
        self.assertFalse(listening(port), "the server --start began is still running")

    def test_start_stops_the_server_when_the_page_fails_to_load(self):
        port = free_port()
        serve = SERVE.replace("{site}", self.site.name)
        result = capture("http://127.0.0.1:{port}/missing.html", "--start", serve, "--port", str(port),
                         "--out", str(self.out))
        self.assertEqual(result.returncode, 2)
        self.assertIn("answered 404", result.stderr)
        self.assertFalse(listening(port), "the server --start began is still running")

    def test_start_stops_a_server_its_command_left_running_in_the_background(self):
        port = free_port()
        serve = SERVE.replace("{site}", self.site.name) + " &"
        result = capture("http://127.0.0.1:{port}/fits.html", "--start", serve, "--port", str(port),
                         "--out", str(self.out))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(listening(port), "the server --start began is still running")

    def test_start_stops_the_server_when_its_terminal_hangs_up(self):
        port = free_port()
        serve = SERVE.replace("{site}", self.site.name)
        run = subprocess.Popen(["node", str(CAPTURE), "http://127.0.0.1:{port}/fits.html", "--start", serve,
                                "--port", str(port), "--wait", "30000", "--out", str(self.out)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 60
            while not listening(port) and time.monotonic() < deadline:
                time.sleep(0.1)
            self.assertTrue(listening(port), "the server never started")
            run.send_signal(signal.SIGHUP)
            run.wait(timeout=30)
        finally:
            run.kill()
            run.communicate()
        time.sleep(0.5)
        self.assertFalse(listening(port), "the server --start began outlived a hang-up")

    def test_a_url_with_a_port_to_fill_needs_start_or_port(self):
        result = capture("http://127.0.0.1:{port}/fits.html", "--out", str(self.out))
        self.assertEqual(result.returncode, 2)
        self.assertIn("give --port, or --start", result.stderr)

    def test_a_page_nothing_serves_exits_2(self):
        result = capture(f"http://127.0.0.1:{free_port()}/", "--out", str(self.out))
        self.assertEqual(result.returncode, 2)
        self.assertIn("couldn't load", result.stderr)


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


if __name__ == "__main__":
    unittest.main()
