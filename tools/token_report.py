#!/usr/bin/env python3
"""Read-only token report for a Kira config backup.

    python3 tools/token_report.py ~/.config/kira-backup-YYYYMMDD-HHMMSS

Prints counts only: no asks, names, emails or other user content.
Kira writes one log row per progress checkpoint; rows sharing an id are folded
to their last version so an ask's usage is counted once.
"""
import json
import os
import sys
from collections import Counter

TOKENS = ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens')
SPECIAL = ('Meeting Copilot', 'Dictation cleanup')


def records(path):
    """Latest row per ask id, plus standalone rows (meeting/dictation) that have no id."""
    folded, standalone = {}, []
    with open(path) as f:
        for line in f:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if not isinstance(row, dict):
                continue
            if row.get('id'):
                folded[row['id']] = row
            else:
                standalone.append(row)
    return list(folded.values()) + standalone


def usage(row):
    """Sum attempt usage; an escalation is one ask with more than one attempt."""
    total = Counter()
    for attempt in row.get('attempt_usage') or []:
        if not isinstance(attempt, dict):
            continue
        u = attempt.get('usage')
        if not isinstance(u, dict):
            continue
        for key in TOKENS:
            value = u.get(key)
            total[key] += value if isinstance(value, int) else 0
    return total


def kind(row):
    task = row.get('task')
    if task in SPECIAL:
        return task
    return 'Main ask'


def usd(row):
    amount = row.get('usd')
    if isinstance(amount, (int, float)):
        return amount
    return sum(v for v in row.get('attempt_usd') or [] if isinstance(v, (int, float)))


def print_totals(title, rows):
    totals = Counter()
    costs = 0.0
    with_usage = 0
    for row in rows:
        u = usage(row)
        if sum(u.values()):
            with_usage += 1
        totals.update(u)
        costs += usd(row)
    fresh, write, read, out = (totals[k] for k in TOKENS)
    counted = fresh + write + read + out
    print(title)
    print(f'  asks: {len(rows)} ({with_usage} with usage)   cost: ${costs:.4f}')
    print(f'  input {fresh:,}   cache write {write:,}   cache read {read:,}   output {out:,}   total {counted:,}')
    if counted:
        for name, value in zip(('fresh input', 'cache write', 'cache read', 'output'), (fresh, write, read, out)):
            print(f'  {name:12} {value / counted:6.1%}')
    if with_usage:
        print(f'  per ask: input {fresh / with_usage:,.0f}   cache write {write / with_usage:,.0f}   '
              f'cache read {read / with_usage:,.0f}   output {out / with_usage:,.0f}   ${costs / with_usage:.4f}')
    return totals, costs


def main():
    if len(sys.argv) != 2:
        return print(__doc__.strip())
    root = sys.argv[1]
    log = os.path.join(root, 'log.jsonl')
    if not os.path.isfile(log):
        return print(f'No log.jsonl in {root}')
    rows = records(log)
    groups = {}
    for row in rows:
        groups.setdefault(kind(row), []).append(row)
    print(f'Kira token report: {root}\n')
    print_totals('All logged requests', rows)
    print()
    for name in ('Main ask',) + SPECIAL:
        if name in groups:
            print_totals(name, groups[name])
            print()

    asks = groups.get('Main ask', [])
    escalated = [row for row in asks if row.get('escalated')]
    print('Balanced escalation')
    print(f'  asks: {len(asks)}   escalated: {len(escalated)} ({len(escalated) / len(asks):.1%})' if asks else '  no main asks')
    if escalated:
        total = sum(usd(row) for row in escalated)
        attempts = sum(max(0, len(row.get('attempt_usage') or []) - 1) for row in escalated)
        print(f'  cost: ${total:.4f}   extra attempts: {attempts}   average: ${total / len(escalated):.4f}')
        for why, count in Counter(row.get('escalate_why') for row in escalated).most_common():
            print(f'  {why or "unknown"}: {count}')
    print()

    states = []
    for name in sorted(os.listdir(os.path.join(root, 'agents'))):
        state = os.path.join(root, 'agents', name, 'state.json')
        try:
            with open(state) as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        followups = 0
        try:
            with open(os.path.join(root, 'agents', name, 'log.jsonl')) as f:
                followups = sum(1 for line in f if '"followup"' in line)
        except OSError:
            pass
        u = data.get('usage') if isinstance(data.get('usage'), dict) else {}
        states.append((data, u, followups))
    totals, costs = Counter(), 0.0
    print('Background agents')
    print(f'  agents: {len(states)}')
    for data, u, followups in states:
        totals.update({k: u.get(k, 0) or 0 for k in TOKENS})
        costs += data.get('cost') if isinstance(data.get('cost'), (int, float)) else 0
    turns = sum(max(0, followups - 1) for _, _, followups in states)   # the first followup event is the brief
    print(f'  cost: ${costs:.4f}   follow-ups: {turns}   followup events: {sum(f for _, _, f in states)}')
    fresh, write, read, out = (totals[k] for k in TOKENS)
    counted = fresh + write + read + out
    print(f'  input {fresh:,}   cache write {write:,}   cache read {read:,}   output {out:,}   total {counted:,}')
    if counted:
        for name, value in zip(('fresh input', 'cache write', 'cache read', 'output'), (fresh, write, read, out)):
            print(f'  {name:12} {value / counted:6.1%}')
    if states:
        print(f'  per agent: cost ${costs / len(states):.4f}   tokens {counted / len(states):,.0f}')
    if turns:
        print(f'  per follow-up: cost ${costs / (len(states) + turns):.4f}   tokens {counted / (len(states) + turns):,.0f}')


if __name__ == '__main__':
    main()
