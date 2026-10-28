# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
"""Idle power: Kira must not keep high-frequency timers or animation loops running while nothing happens.
Source-only checks; no app, window or audio is started."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class IdlePowerTests(unittest.TestCase):
    def test_shelf_clock_runs_fast_only_while_agents_are_on_it(self):
        swift = (ROOT / 'Kira.swift').read_text()
        self.assertIn('var rows: [String:[String:Any]] = [:] { didSet { scheduleTick() } }', swift)
        schedule = swift.split('func scheduleTick()', 1)[1].split('func tick()', 1)[0]
        self.assertIn('rows.isEmpty ? 1 : 0.1', schedule)
        self.assertIn('timer?.tolerance = interval / 10', schedule)
        self.assertNotIn('withTimeInterval:0.1, repeats:true) { [weak self] _ in self?.tick() }', swift)

    def test_agents_watch_loop_slows_down_with_no_running_agent(self):
        source = (ROOT / 'kira.py').read_text()
        self.assertIn('manager.tick(); time.sleep(.15 if manager.processes else 1)', source)

    def test_globe_repaints_slowly_while_resting(self):
        page = (ROOT / 'ui' / 'ui.html').read_text()
        self.assertIn("const resting = boost === 1 && state === 'breathing';", page)
        self.assertIn('if (now - drawn > (resting ? 80 : 30) || reduced.matches)', page)
        self.assertIn('visible && !reduced.matches ? (resting ? 90 : 0) : 250', page)

    def test_crash_audio_watch_coalesces_with_other_timers(self):
        swift = (ROOT / 'Kira.swift').read_text()
        self.assertIn('watch.tolerance = 1', swift)


if __name__ == '__main__':
    unittest.main()
