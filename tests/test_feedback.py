# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
"""Feedback privacy and instant routing; no browser or AI calls."""
import io
import json
import os
import subprocess
import unittest
import urllib.parse
from unittest.mock import patch
import kira
from tests import scratch_dir


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.root = scratch_dir(self)
        for p in [patch.object(kira.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'Mac14,5\n')),
                  patch.object(kira.platform, 'mac_ver', return_value=('26.0', (), ''))]:
            p.start(); self.addCleanup(p.stop)
        (self.root / 'log.jsonl').write_text(json.dumps({'task': 'Private ask /Users/person/name', 'reply': 'PRIVATE ANSWER', 'ran': ['PRIVATE COMMAND'], 'steps': ['Searching the web: PRIVATE QUERY']})+'\n'+json.dumps({'task': 'report feedback'})+'\n')

    def test_default_contains_only_template_and_whitelisted_environment(self):
        report = kira.feedback({'version': '9429210'})
        self.assertFalse(report['include'])
        self.assertIn('Mac model: Mac14,5', report['body'])
        self.assertIn('Version / commit: 9429210', report['body'])
        self.assertIn('Version: ' + kira.APP_VERSION, report['body']); self.assertIn('Routing: ', report['body'])
        self.assertNotIn('Install ID', report['body'])   # the issue is public: never link it to the anonymous stats
        for secret in ['Private ask', '/Users', 'PRIVATE ANSWER', 'PRIVATE COMMAND', str(self.root)]:
            self.assertNotIn(secret, report['body']); self.assertNotIn(urllib.parse.quote(secret), report['url'])
        if report['url']:   # a project address opens a prefilled issue; without one Settings copies the report instead
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(report['url']).query)
            self.assertEqual(query['body'], [report['body']])
        self.assertIn('What happened', report['body']); self.assertIn('What you expected', report['body'])

    def test_opt_in_shows_exact_previous_ask_only(self):
        report = kira.feedback({'include': True})
        self.assertIn('Private ask /Users/person/name', report['body'])
        self.assertNotIn('PRIVATE QUERY', report['body'])   # step names quote screen content and searches
        self.assertNotIn('PRIVATE ANSWER', report['body']); self.assertNotIn('PRIVATE COMMAND', report['body'])
        self.assertNotIn('report feedback', report['body'])
        self.assertTrue(report['include'])

    def test_feedback_always_waits_for_confirmation_and_skips_ai(self):
        for request in ('report feedback', 'report a bug'):
            with patch('sys.argv', ['kira.py', request]), patch.object(kira, 'start_claude') as ai, patch.object(kira, 'licensed') as license, patch.object(kira, 'wait_commit', return_value=True) as gate, patch('sys.stdout', new_callable=io.StringIO) as out, patch.object(kira, 'look', return_value=[]), patch.object(kira, 'hands_map', return_value=None):
                kira.main()
                ai.assert_not_called(); license.assert_not_called(); gate.assert_called_once()
                self.assertIn('! feedback', out.getvalue())
                self.assertIn('Review your feedback', out.getvalue())
            with patch.dict(os.environ, {'KIRA_LIVE': '1'}, clear=True), patch('sys.stdout', new_callable=io.StringIO) as out:
                self.assertIsNone(kira.fast(request)); self.assertEqual(out.getvalue(), '')
