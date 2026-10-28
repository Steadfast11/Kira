# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
"""Offline completion checks; fake workers and no host apps or AI calls."""
import io
import json
import unittest
from unittest.mock import patch
import kira
from tests import scratch_dir


class ReviewCompletionTests(unittest.TestCase):
    def setUp(self):
        self.root = scratch_dir(self)

    def test_unknown_logout_client_never_signs_out_of_claude(self):
        for client in ('devin', 'pi', 'server', '', 'typo'):
            with self.subTest(client=client), patch.object(kira.shutil, 'which', return_value='/fixture/claude'), patch.object(kira.subprocess, 'run') as run:
                self.assertFalse(kira.account_logout(client)['ok'])
                run.assert_not_called()

    def test_meeting_ignores_malformed_stream_events_and_finishes(self):
        from types import SimpleNamespace
        rows = [[], None, {'type': 'stream_event', 'event': []}, {'type': 'stream_event', 'event': {'delta': []}},
                {'type': 'stream_event', 'event': {'type': 'content_block_delta', 'delta': {'type': 'text_delta', 'text': 3}}},
                {'type': 'result', 'result': 'ANSWER\nFixture answer.'}]
        worker = SimpleNamespace(stdin=io.StringIO(), stdout=iter(json.dumps(row) + '\n' for row in rows), wait=lambda timeout: 0)
        with patch.object(kira, 'client', return_value='claude'), patch.object(kira, 'meeting_process', return_value=worker), \
             patch.object(kira, 'stop_claude') as stop, patch.object(kira.signal, 'signal'), patch.object(kira.atexit, 'register'), \
             patch.object(kira, 'log_turn'), patch('sys.stdin', io.StringIO('{"question":"fixture"}')), patch('sys.stdout', new_callable=io.StringIO) as out:
            kira.meeting_live()
        self.assertEqual(json.loads(out.getvalue().splitlines()[-1])['result']['lines'], ['Fixture answer.'])
        stop.assert_called_with(worker)

    def test_meeting_rejects_malformed_request_and_terminal_result_honestly(self):
        from types import SimpleNamespace
        for request, answer in (('[]', 'answer'), ('{}', []), ('{}', {'unexpected': 'shape'})):
            worker = SimpleNamespace(stdin=io.StringIO(), stdout=iter([json.dumps({'type': 'result', 'result': answer})]), wait=lambda timeout: 0)
            with self.subTest(request=request, answer=answer), patch.object(kira, 'client', return_value='claude'), \
                 patch.object(kira, 'meeting_process', return_value=worker), patch.object(kira, 'stop_claude') as stop, \
                 patch.object(kira.signal, 'signal'), patch.object(kira.atexit, 'register'), patch.object(kira, 'log_turn'), \
                 patch('sys.stdin', io.StringIO(request)), patch('sys.stdout', new_callable=io.StringIO) as out:
                kira.meeting_live()
                self.assertTrue(json.loads(out.getvalue().splitlines()[-1])['result']['error'])
                stop.assert_called_with(worker)

    def test_codex_null_content_is_not_the_end_of_input(self):
        from tests.test_review_reliability import ReviewReliabilityTests
        fixture = ReviewReliabilityTests(); fixture.root = self.root
        events = fixture.shim([{'type': 'user', 'message': {'content': None}}, {'type': 'user', 'message': {'content': 'next'}}],
                              'print(json.dumps({"type":"item.completed","item":{"type":"agent_message","text":"next answer"}}))\n'
                              'print(json.dumps({"type":"turn.completed"}))\n')
        self.addCleanup(fixture.doCleanups)
        results = [e for e in events if e['type'] == 'result']
        self.assertEqual([e['is_error'] for e in results], [True, False])
        self.assertEqual(results[-1]['result'], 'next answer')
