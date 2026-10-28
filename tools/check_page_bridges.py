# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
"""Check literal WebKit actions/calls; dynamic payloads still need the page harnesses."""
from pathlib import Path
import ast
import re

ROOT = Path(__file__).resolve().parents[1]
PAGES = {'st': ('settings', 'SettingsWindow'), 'ob': ('onboarding', 'Onboarding'),
         'boot': ('boot', 'Boot'), 'ui': ('ui', 'App'), 'meeting': ('meeting', 'MeetingCopilot'),
         'agents': ('agents', 'AgentPanels'), 'setup': ('setup', 'SetupFlow')}


def class_source(source, name):
    start = source.index('final class ' + name + ':') if 'final class ' + name + ':' in source else source.index('final class ' + name + ' {')
    end = re.search(r'^final class |^struct |^// `Kira ', source[start + 1:], re.M)
    return source[start:start + 1 + end.start()] if end else source[start:]


def check(root=ROOT):
    swift = (root / 'Kira.swift').read_text()
    tree = ast.parse((root / 'kira.py').read_text())
    agent = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'Agents')
    command = next(node for node in agent.body if isinstance(node, ast.FunctionDef) and node.name == 'command')
    worker_actions = set()
    for node in ast.walk(command):
        if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name) and node.left.id == 'action':
            for value in node.comparators:
                for item in value.elts if isinstance(value, (ast.Tuple, ast.List)) else [value]:
                    if isinstance(item, ast.Constant) and isinstance(item.value, str): worker_actions.add(item.value)
    problems, inventory = [], {}
    for namespace, (page, owner) in PAGES.items():
        html = (root / 'ui' / (page + '.html')).read_text()
        if '/*SETUP*/' in html: html = html.replace('/*SETUP*/', (root / 'ui/setup.js').read_text())
        native = class_source(swift, owner)
        methods = set(re.findall(r'\b([A-Za-z_]\w*)\s*\([^()\n]*\)\s*\{', html))
        methods.update(re.findall(r'\b([A-Za-z_]\w*)\s*:\s*(?:function\b|\([^\n]*?\)\s*=>|[A-Za-z_]\w*\s*=>)', html))
        calls = set(re.findall(r'"' + namespace + r'\.([A-Za-z_]\w*)\s*(?:\(|"\s*,)', swift))
        if namespace == 'setup': calls.update(re.findall(r'\bcall\("(\w+)"', native))
        if namespace == 'st': calls.update(re.findall(r'\bsend\("(\w+)"', native))
        if namespace in ('ui', 'meeting'): calls.update(re.findall(r'\bjs\("(\w+)"', native))
        if namespace == 'agents': calls.update(re.findall(r'\bjs\([^\n,]+,\s*"(\w+)"', native))
        actions = set(re.findall(r'\bdo\s*:\s*[\'"]([\w-]+)[\'"]|data-do=[\'"]([\w-]+)[\'"]', html))
        actions = {a or b for a, b in actions}
        if namespace == 'ui': actions.update(re.findall(r'\bpost\(\s*\{\s*(\w+)\s*:', html))
        if namespace in ('agents', 'setup'):
            actions.update(re.findall(r'\baction\s*:\s*[\'"]([\w-]+)[\'"]', html))
            actions.update(re.findall(r'\bcommand\(\s*[\'"]([\w-]+)[\'"]', html))
        handled = set()
        for line in re.findall(r'case\s+([^:\n]+):', native): handled.update(re.findall(r'"([\w-]+)"', line))
        handled.update(re.findall(r'\["do"\]\s*==\s*"([\w-]+)"', native))
        for line in re.findall(r'\[[^\n]+\]\.contains\(d\)', native): handled.update(re.findall(r'"([\w-]+)"', line))
        if namespace == 'ui': handled.update(re.findall(r'\bb\["(\w+)"\]', native))
        if namespace == 'agents': handled.update(worker_actions)
        if namespace == 'ob': handled.add('grant')   # permission IDs dispatch through grant(b["id"])
        for action in sorted(actions - handled): problems.append(f'{page}: action {action} has no native handler')
        for call in sorted(calls - methods): problems.append(f'{page}: native call {namespace}.{call} has no page function')
        inventory[page] = {'actions': sorted(actions), 'handlers_without_literal_action': sorted(handled - actions), 'native_calls': sorted(calls)}
    return problems, inventory


if __name__ == '__main__':
    import json
    problems, inventory = check()
    print(json.dumps({'problems': problems, 'inventory': inventory}, indent=2))
    raise SystemExit(bool(problems))
