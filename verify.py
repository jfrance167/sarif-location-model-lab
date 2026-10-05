"""Repeatable local verification; writes fresh evidence, never overwrites it.

Usage: python verify.py FRESH_DIRECTORY
Runs installed Python/Bandit on owned source and inert fixtures only. No installs,
network, target execution or model-generated executable inputs are involved.
"""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def command(args, destination):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=90, check=False)
    destination.with_suffix('.stdout').write_bytes(result.stdout)
    destination.with_suffix('.stderr').write_bytes(result.stderr)
    return {'argv': args, 'exit': result.returncode}


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python verify.py FRESH_DIRECTORY')
    destination = Path(sys.argv[1]).resolve()
    if not destination.is_relative_to(ROOT):
        raise SystemExit('Evidence must stay within this project.')
    destination.mkdir(parents=True, exist_ok=False)
    results = {}
    for mode, flags in [('normal', []), ('optimized', ['-O'])]:
        results[mode] = command([sys.executable, *flags, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], destination/mode)
    source = (ROOT/'model.py').read_text(encoding='utf-8')
    for name, allowed in [('model.py', {'json', 're'}), ('cli.py', {'sys', 'model'})]:
        tree = ast.parse((ROOT/name).read_text(encoding='utf-8'))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {'open', 'eval', 'exec', '__import__', 'compile'}:
                raise RuntimeError('Forbidden application call')
        if set(imports) != allowed:
            raise RuntimeError('Unexpected application imports')
    results['application_imports'] = 'exact allowlists passed'
    cases = json.loads((ROOT/'tests/oracles.json').read_text(encoding='utf-8'))
    edits = [
        ('index_range', "if value['index'] >= table_count:", 'if False:', 'index_out_of_range'),
        ('base_cycle', 'if current in chain:', 'if False:', 'unused_cycle'),
        ('guessed_end', "'end_column': region.get('endColumn'),", "'end_column': region.get('endColumn', 1),", 'unknown_end'),
        ('erased_unit', "'column_kind': kind,", "'column_kind': 'utf16CodeUnits',", 'codepoint_units'),
    ]
    mutations = []
    for name, original, replacement, case_name in edits:
        if source.count(original) != 1:
            raise RuntimeError('Mutation anchor changed')
        mutation = destination/name
        mutation.mkdir()
        (mutation/'model.py').write_text(source.replace(original, replacement), encoding='utf-8', newline='\n')
        case = next(item for item in cases if item['name'] == case_name)
        (mutation/'case.json').write_text(json.dumps(case), encoding='utf-8')
        # Golden expectation supplied as data, never calculated by the mutant.
        probe = """import json
import unittest
from pathlib import Path
import model
case = json.loads(Path(__file__).with_name('case.json').read_text())
class Oracle(unittest.TestCase):
    def test_intended_semantic_change(self):
        self.assertEqual(model.interpret(case['input']), case['expected'], 'FROZEN_ORACLE_MISMATCH')
unittest.main()
"""
        (mutation/'probe.py').write_text(probe, encoding='utf-8')
        run = command([sys.executable, str(mutation/'probe.py')], mutation/'result')
        log = (mutation/'result.stderr').read_text(encoding='utf-8')
        killed = (run['exit'] == 1 and 'AssertionError:' in log and
                  'FROZEN_ORACLE_MISMATCH' in log and 'FAILED (failures=1)' in log and 'ERROR:' not in log)
        mutations.append({'mutation': name, 'case': case_name, 'assertion_killed': killed, 'exit': run['exit']})
    results['mutations'] = mutations
    results['source_unchanged'] = (ROOT/'model.py').read_text(encoding='utf-8') == source
    for name, args in [('bandit_application', ['model.py', 'cli.py']),
                       ('bandit_harness', ['verify.py', 'tests/test_model.py', 'research/author_oracles.py'])]:
        results[name] = command([sys.executable, '-m', 'bandit', *args, '-f', 'json'], destination/name)
    # Actual child stdout pipe is closed before input, exercising interpreter exit.
    child = subprocess.Popen([sys.executable, str(ROOT/'cli.py')], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    child.stdout.close()
    child.stdin.write(json.dumps(cases[0]['input']).encode())
    child.stdin.close()
    child.stdin = None
    child.stdout = None
    try:
        _, error = child.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        child.kill()
        child.communicate(timeout=10)
        raise
    exit_code = child.returncode
    (destination/'closed-pipe.stderr').write_bytes(error)
    results['actual_closed_pipe'] = {'exit': exit_code, 'fixed_diagnostic': error in (
        b'Input or output operation failed.\n', b'Input or output operation failed.\r\n')}
    files = ['model.py', 'cli.py', 'verify.py', 'tests/test_model.py', 'tests/oracles.json', 'CONTRACT.md', 'research/oracle-freeze.json']
    results['files'] = [{'path': name, 'length': (ROOT/name).stat().st_size,
                         'sha256': hashlib.sha256((ROOT/name).read_bytes()).hexdigest()} for name in files]
    results['runtime'] = sys.version
    passed = (results['normal']['exit'] == results['optimized']['exit'] == 0 and
              all(item['assertion_killed'] for item in mutations) and results['source_unchanged'] and
              results['bandit_application']['exit'] == 0 and exit_code == 3 and
              results['actual_closed_pipe']['fixed_diagnostic'])
    results['passed'] = passed
    (destination/'receipt.json').write_text(json.dumps(results, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'passed': passed, 'tests': [results[m]['exit'] for m in ('normal', 'optimized')],
                      'mutations': mutations, 'closed_pipe': results['actual_closed_pipe'],
                      'bandit': [results[m]['exit'] for m in ('bandit_application', 'bandit_harness')]}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
