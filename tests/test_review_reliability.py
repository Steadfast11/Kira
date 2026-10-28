# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
"""Offline review regressions; no real AI, accounts, or host windows."""
import io
import json
import os
import unittest
from unittest.mock import patch
import kira
from tests import scratch_dir


class ReviewReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.root = scratch_dir(self)

    def test_malformed_hook_events_use_each_clients_deny_shape(self):
        for client in ('codex', 'claude', 'devin', 'pi'):
            for raw in ('{', '[]', '{"tool_input":[]}', '{"tool_input":{"command":3}}', '{"tool_name":null}', '{"tool_name":[]}', '{"tool_name":""}'):
                with self.subTest(client=client, raw=raw), patch.dict(os.environ, {'KIRA_CLIENT': client}), \
                     patch('sys.stdin', io.StringIO(raw)), patch('sys.stdout', new_callable=io.StringIO) as out:
                    if client in ('codex', 'devin', 'pi'):
                        with self.assertRaises(SystemExit) as stopped: kira.gate()
                        self.assertEqual(stopped.exception.code, 2)
                    else: kira.gate()
                    result = json.loads(out.getvalue())
                    if client in ('codex', 'claude'):
                        self.assertEqual(result['hookSpecificOutput']['permissionDecision'], 'deny')
                    else: self.assertEqual(result['decision'], 'block')

    def shim(self, messages, program):
        import sys
        fake = self.root / 'codex'
        fake.write_text('#!' + sys.executable + '\nimport json, sys\n'
                        'if sys.argv[1:3] == ["features", "list"]: raise SystemExit(0)\n'
                        'sys.stdin.read()\n' + program)
        fake.chmod(0o755)
        env = {**os.environ, 'PATH': str(self.root) + os.pathsep + os.environ['PATH'], 'KIRA_DIR': str(self.root)}
        p = kira.codex_process('main', 'fixture', str(self.root), env)
        self.addCleanup(kira.stop_claude, p)
        out, err = p.communicate(''.join(json.dumps(m) + '\n' for m in messages), timeout=10)
        self.assertEqual(p.returncode, 0, err)
        return [json.loads(line) for line in out.splitlines()]

    def test_codex_late_failure_does_not_report_success(self):
        events = self.shim([{'type': 'user', 'message': {'content': 'hello'}}],
                           'print(json.dumps({"type":"turn.completed"}))\n'
                           'print(json.dumps({"type":"error","message":"worker failed"}))\nraise SystemExit(1)\n')
        self.assertTrue(events[-1]['is_error'])
        self.assertIn('worker failed', events[-1]['result'])

    def test_codex_unavailable_removes_image_copies(self):
        import base64
        message = {'type': 'user', 'message': {'content': [{'type': 'image', 'source': {'type': 'base64', 'data': base64.b64encode(b'fixture').decode()}}]}}
        with patch.object(kira, 'codex_bin', return_value=None), patch.object(kira.os, 'getcwd', return_value=str(self.root)), \
             patch('sys.stdin', io.StringIO(json.dumps(message) + '\n')), patch('sys.stdout', new_callable=io.StringIO) as out:
            kira.codex_shim()
        self.assertEqual(list(self.root.glob('kira-codex-*')), [])
        self.assertTrue(json.loads(out.getvalue())['is_error'])

    def test_codex_bad_image_does_not_lose_the_next_turn(self):
        events = self.shim([{'type': 'user', 'message': {'content': [{'type': 'image', 'source': {'type': 'base64', 'data': 'a'}}]}},
                            {'type': 'user', 'message': {'content': 'next'}}],
                           'print(json.dumps({"type":"item.completed","item":{"type":"agent_message","text":"next answer"}}))\n'
                           'print(json.dumps({"type":"turn.completed"}))\n')
        results = [e for e in events if e['type'] == 'result']
        self.assertEqual([e['is_error'] for e in results], [True, False])
        self.assertEqual(results[-1]['result'], 'next answer')
        self.assertEqual(list(self.root.glob('kira-codex-*')), [])

    def test_codex_malformed_control_does_not_stop_input_reader(self):
        events = self.shim([{'type': 'control_request', 'request': [1]}, {'type': 'user', 'message': [1]},
                            {'type': 'user', 'message': {'content': 'next'}}],
                           'print(json.dumps({"type":"item.completed","item":{"type":"agent_message","text":"answer"}}))\n'
                           'print(json.dumps({"type":"turn.completed"}))\n')
        self.assertEqual([e['result'] for e in events if e['type'] == 'result'], ['answer'])

    def test_claude_plan_rejects_malformed_status_without_crashing(self):
        import subprocess
        for status in ([], None, 'signed in', {'loggedIn': True, 'authMethod': 'claude.ai', 'subscriptionType': 3}):
            with self.subTest(status=status), patch.object(kira, 'server', return_value={}), \
                 patch.object(kira.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps(status), '')):
                self.assertFalse(kira.claude_plan()['ok'])
        with patch.object(kira, 'server', return_value={}), patch.object(kira.subprocess, 'run', side_effect=PermissionError('fixture')):
            self.assertFalse(kira.claude_plan()['ok'])

    def test_agent_followup_write_failure_finishes_instead_of_escaping(self):
        agents = kira.Agents(emit=lambda e: None)
        row = agents.new(); row.update(status='running', brief='fixture')
        agents.rows[row['id']] = row
        with patch.object(agents, 'send', side_effect=BrokenPipeError('fixture pipe')), patch.object(kira, 'close_agent_window'):
            agents.start(row['id'], 'followup')
        self.assertEqual(row['status'], 'failed')
        self.assertIn('fixture pipe', row['result'])

    def test_meeting_launch_failure_emits_a_result(self):
        with patch.object(kira, 'client', return_value='claude'), patch.object(kira, 'meeting_process', side_effect=FileNotFoundError('fixture')), \
             patch('sys.stdin', io.StringIO('{"question":"hello"}')), patch('sys.stdout', new_callable=io.StringIO) as out:
            kira.meeting_live()
        result = json.loads(out.getvalue())
        self.assertEqual(result['event'], 'result')
        self.assertTrue(result['result']['error'])

    def test_meeting_connector_probe_launch_failure_keeps_local_brief(self):
        with patch.object(kira, 'client', return_value='claude'), patch.object(kira.shutil, 'which', return_value='/fixture/claude'), \
             patch.object(kira.subprocess, 'Popen', side_effect=PermissionError('fixture')):
            result = kira.meeting_gather({'text': 'Local notes'})
        self.assertIn('Local notes', result['brief'])
        self.assertIn('unavailable', result['notice'])

    def test_malformed_ai_recap_keeps_the_local_summary(self):
        folder = self.root / 'meetings' / 'fixture'; folder.mkdir(parents=True)
        (folder / 'metadata.json').write_text(json.dumps({'started': 1, 'title': 'Fixture'}))
        (folder / 'events.jsonl').touch()
        kira.meeting_append('fixture', {'kind': 'transcript', 'text': 'Opening words', 'seconds': 0})
        with patch.object(kira, 'client', return_value='claude'), patch.object(kira.shutil, 'which', return_value='/fixture/claude'), \
             patch.object(kira, 'meeting_call', return_value=('[]', {})):
            result = kira.meeting_finish('fixture')
        self.assertIn('Opening words', result['summary'])
        self.assertEqual(len(result['transcript']), 1)

    def test_build_stages_and_signs_resources_before_replacing_the_app(self):
        from pathlib import Path
        source = (Path(kira.ME).parent / 'build.sh').read_text()
        stage = source.index('APP="$STAGE/Kira.app"')
        sign = source.index('codesign -s')
        promote = source.index('mv "$APP" "$TARGET"')
        self.assertLess(stage, source.index('cp kira.py'))
        self.assertLess(sign, promote)
        self.assertIn('codesign --verify --strict "$APP"', source[sign:promote])
        self.assertIn('previous.app', source)

    def test_bundle_promotion_rolls_back_on_failure(self):
        import subprocess
        from pathlib import Path
        source = (Path(kira.ME).parent / 'build.sh').read_text()
        cleanup = source[source.index('cleanup() {'):source.index("trap 'exit 1' HUP INT TERM")]
        promote = source[source.index('if [ -e "$TARGET" ]; then mv'):source.index('APP="$TARGET"')]
        for fails in (False, True):
            with self.subTest(fails=fails):
                stage = self.root / ('stage-' + str(fails)); stage.mkdir()
                target = self.root / ('installed-' + str(fails)); target.mkdir(); (target / 'old').touch()
                app = stage / 'Kira.app'; app.mkdir(); (app / 'new').touch()
                failure = 'mv() { if [ "$1" = "$APP" ]; then return 1; fi; command mv "$@"; }\n' if fails else ''
                script = 'set -e\n' + cleanup + failure + promote
                done = subprocess.run(['/bin/bash', '-c', script], env={**os.environ, 'STAGE': str(stage), 'TARGET': str(target), 'APP': str(app)}, capture_output=True, text=True)
                self.assertEqual(done.returncode, 1 if fails else 0, done.stderr)
                self.assertTrue((target / ('old' if fails else 'new')).exists())
                self.assertFalse(stage.exists())

    def test_installer_requires_sources_and_stops_on_build_failure(self):
        from pathlib import Path
        source = (Path(kira.ME).parent / 'install.sh').read_text()
        self.assertIn('[ -f "$DIR/build.sh" ]', source)
        self.assertIn('"$DIR/build.sh" ||', source)
        failure = source.split('"$DIR/build.sh" ||', 1)[1].split('\n', 1)[0]
        self.assertIn('exit 1', failure)

    def test_codex_does_not_claim_unsupported_control_requests_succeeded(self):
        events = self.shim([{'type': 'control_request', 'request_id': 'tools', 'request': {'subtype': 'mcp_set_servers', 'servers': {}}}], '')
        self.assertEqual(events[0]['response']['subtype'], 'error')
        self.assertIn('not supported', events[0]['response']['error'])

    def test_codex_errors_name_the_selected_client(self):
        from types import SimpleNamespace
        for detail in ('429 Too Many Requests', 'Authentication failed', 'network connection failed', 'service unavailable'):
            worker = SimpleNamespace(stdin=io.StringIO(), stdout=io.StringIO(json.dumps({'type': 'result', 'is_error': True, 'result': detail}) + '\n'),
                                     errors=io.StringIO(), returncode=0, wait=lambda timeout: 0)
            with self.subTest(detail=detail), patch.object(kira, 'client', return_value='codex'), patch.object(kira, 'say'), patch.object(kira, 'server', return_value={}):
                reply, _, _ = kira.run('fixture', worker)
            self.assertNotIn('Claude', reply)
            self.assertIn('Codex', reply)

    def test_onboarding_ignores_models_from_an_old_server_probe(self):
        import subprocess
        from pathlib import Path
        source = (Path(kira.ME).parent / 'ui/onboarding.html').read_text()
        method = source[source.index('    models('):source.index('    local(list)')].rstrip().rstrip(',')
        script = '''const assert=require('assert');
const nodes={'srv-base':{value:'new'},'srv-key':{value:'key'},'srv-models':{replaceChildren(...v){this.items=v}},'srv-model':{value:''},'srv-note':{classList:{toggle(){}}}};
const $=id=>nodes[id],document={createElement:()=>({})},paintProv=()=>{};
const ob={''' + method + '''};
ob.models({base:'old',key:'key',list:['stale']});assert.equal(nodes['srv-model'].value,'');
ob.models({base:'new',key:'old-key',list:['stale']});assert.equal(nodes['srv-model'].value,'');
ob.models({base:'new',key:'key',list:['fresh']});assert.equal(nodes['srv-model'].value,'fresh');
'''
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_paused_supervisor_does_not_drain_queued_agents(self):
        agents = kira.Agents(emit=lambda e: None)
        row = agents.new(); row.update(status='queued', brief='fixture')
        agents.rows[row['id']] = row
        with patch.object(agents, 'start') as start, patch.object(kira, 'pref', side_effect=lambda k, d: True if k == 'paused' else d):
            agents.drain(); start.assert_not_called()
        with patch.object(agents, 'start') as start:
            agents.drain(); start.assert_called_once_with(row['id'], None)
