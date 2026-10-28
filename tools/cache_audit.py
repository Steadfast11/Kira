#!/usr/bin/env python3
"""Offline full Kira request-prefix audit; no client process, user data or network."""
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('KIRA_DIR', tempfile.mkdtemp(prefix='kira-cache-audit-'))
import kira


def request_prefix(request, app, title, context, main_only=False):
    # Match run(): user_content plus the conditional main-window delivery block, before explicit user words.
    system = kira.system_prompt(kira.ASK_FIRST)
    blocks = kira.user_content(f'Context: Front app: {app}. Front window: {title}. Now: {context}\n', request=request)
    if main_only:
        blocks.insert(0, {'type': 'text', 'text': 'This request requires main-window delivery. Finish here; do not emit agent, steer, or agent-profile run directives.'})
    prefix = ''.join(b['text'].split('THE CURRENT USER REQUEST (do this now):\n')[0] for b in blocks)
    return system, prefix


def main():
    with patch.object(kira, 'pref', side_effect=lambda key, default: default):
        first = request_prefix('Summarize this document.', 'Fixture Editor', 'notes.txt', 'Monday. ' + 'document context ' * 100)
        second = request_prefix('Find the total.', 'Fixture Sheets', 'totals.csv', 'Tuesday. ' + 'table context ' * 80)
    common = os.path.commonprefix([a + b for a, b in (first, second)])
    print(json.dumps({'system_identical': first[0] == second[0], 'stable_system_chars': len(first[0]),
                      'full_prefix_common_chars': len(common), 'variable_prefix_chars': [len(p[1]) for p in (first, second)],
                      'expected_kira_dynamic_tokens_chars_over_4': [len(p[1]) / 4 for p in (first, second)],
                      'helper_path_chars': len(kira.ME), 'system_helper_occurrences': kira.SYSTEM.count(kira.ME)}, indent=2))


if __name__ == '__main__': main()
