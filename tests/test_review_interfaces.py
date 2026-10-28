# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
"""Live exported WebKit interfaces in offscreen views; no windows or AI."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from tests.test_settings_page import HARNESS
from tools.check_page_bridges import ROOT, PAGES, check


@unittest.skipUnless(sys.platform == 'darwin', 'macOS WebKit check')
class ReviewInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(); cls.folder = Path(cls.temp.name)
        cls.binary = cls.folder / 'interfaces'
        source = HARNESS.replace('cfg.userContentController.add(h, name: "st")',
                                'for name in ["st","ob","boot","c","h","agents","meeting","setup"] { cfg.userContentController.add(h, name:name) }')
        source = source.replace('let nsapp = NSApplication.shared', 'let nsapp = NSApplication.shared\nnsapp.setActivationPolicy(.prohibited)')
        path = cls.folder / 'interfaces.swift'; path.write_text(source)
        result = subprocess.run(['swiftc', str(path), '-o', str(cls.binary)], capture_output=True, text=True, timeout=60)
        if result.returncode: raise AssertionError(result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_all_native_page_calls_are_exported_functions(self):
        _, inventory = check()
        for namespace, (page, _) in PAGES.items():
            with self.subTest(page=page):
                html = (ROOT / 'ui' / (page + '.html')).read_text()
                for marker, asset in [('/*ORBS*/','orbs.js'),('/*ORB*/','orb.js'),('/*GLOBE*/','globe.js'),('/*CATALOG*/','catalog.js'),('/*VOICE*/','boot/timings.json'),('/*SETUP*/','setup.js')]:
                    if marker in html: html = html.replace(marker, (ROOT / 'ui' / asset).read_text())
                path = self.folder / (page + '.html'); path.write_text(html)
                calls = json.dumps(inventory[page]['native_calls'])
                script = 'await new Promise(r=>setTimeout(r,50));return ' + calls + '.filter(k=>typeof window[' + json.dumps(namespace) + ']?.[k]!=="function");'
                result = subprocess.run([str(self.binary), str(path), script], capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout.strip().splitlines()[-1])['result'], [], page)
