"""Full independent golden reports plus boundary and delivery checks."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import unittest
from unittest.mock import patch

import cli
import model

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT/'tests/oracles.json').read_text(encoding='utf-8'))


def sample():
    return copy.deepcopy(CASES[0]['input'])


def physical(value):
    return value['sarif']['runs'][0]['results'][0]['locations'][0]['physicalLocation']


class Oracles(unittest.TestCase):
    def test_full_reports(self):
        for case in CASES:
            with self.subTest(case=case['name']):
                self.assertEqual(model.interpret(case['input']), case['expected'])

    def test_frozen_hashes(self):
        for entry in json.loads((ROOT/'research/oracle-freeze.json').read_text(encoding='utf-8-sig')):
            self.assertEqual(hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest(), entry['sha256'])

    def test_real_cli_all_oracles(self):
        for case in CASES:
            with self.subTest(case=case['name']):
                run = subprocess.run([sys.executable, str(ROOT/'cli.py')],
                                     input=json.dumps(case['input']).encode(),
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     timeout=10, check=False)
                self.assertEqual(run.returncode, 0 if case['expected']['status'] == 'interpreted' else 2)
                self.assertEqual(run.stderr, b'')
                self.assertEqual(json.loads(run.stdout), case['expected'])


class Admission(unittest.TestCase):
    def test_decoder_rejections(self):
        for raw in (b'{"x":1,"x":2}', b'\xef\xbb\xbf{}', b'{"x":NaN}',
                    b'{"x":1.2}', b'{"x":10000000000}', b'{"x":"\\ud800"}',
                    b'\xff', b'[] trailing', b'['*17+b']'*17, b' '*65537):
            with self.subTest(raw=raw[:40]):
                with self.assertRaises(model.Invalid):
                    model.decode(raw)

    def test_raw_exact_byte_limit(self):
        raw = json.dumps(sample(), separators=(',', ':')).encode()
        self.assertEqual(model.interpret(model.decode(raw+b' '*(65536-len(raw))))['status'], 'interpreted')
        with self.assertRaises(model.Invalid):
            model.decode(raw+b' '*(65537-len(raw)))

    def test_api_custom_cycle_and_nonjson(self):
        class Hostile(dict):
            def items(self):
                raise RuntimeError('must not iterate')
        cycle = []; cycle.append(cycle)
        for value in (Hostile(), cycle, (1,), {1: 2}, {'x': float('inf')}, {'x': -1}, {'x': 2**31}):
            self.assertEqual(model.interpret(value)['status'], 'invalid')

    def test_node_string_depth_bounds(self):
        for value in ({'x': [None]*4096}, {'x': 'a'*1025}, {'x': '\udfff'}):
            self.assertEqual(model.interpret(value)['status'], 'invalid')
        nested = None
        for _ in range(17):
            nested = [nested]
        self.assertEqual(model.interpret(nested)['status'], 'invalid')

    def test_unknown_field_escaped_pointer(self):
        d = sample(); d['a~/b'] = 1
        self.assertEqual(model.interpret(d)['reasons'], [{'code': 'unknown_field', 'pointer': '/a~0~1b'}])

    def test_envelope_and_null_runs(self):
        for key, value, code in [('profile', 'future', 'profile'), ('schema_version', 2, 'schema_version')]:
            d = sample(); d[key] = value
            self.assertEqual(model.interpret(d)['status'], 'unsupported')
            self.assertEqual(model.interpret(d)['reasons'][0]['code'], code)
        d = sample(); d['schema_version'] = True
        self.assertEqual(model.interpret(d)['status'], 'invalid')
        d = sample(); d['sarif']['runs'] = None
        self.assertEqual(model.interpret(d)['reasons'][0]['code'], 'runs_null')
        d['sarif']['runs'] = []
        self.assertEqual(model.interpret(d), {'schema_version': 1, 'status': 'interpreted', 'reasons': [], 'runs': []})


class References(unittest.TestCase):
    def test_unknown_dual_agreement(self):
        d = sample(); run = d['sarif']['runs'][0]
        run['artifacts'] = [{'location': {'uri': 'a.c', 'uriBaseId': 'ROOT'}}]
        physical(d)['artifactLocation']['index'] = 0
        out = model.interpret(d)
        self.assertEqual(out['status'], 'incomplete')
        a = out['runs'][0]['results'][0]['locations'][0]['artifact']
        self.assertEqual(a['agreement'], 'unknown')
        self.assertEqual(a['index']['reference']['chain'], ['ROOT'])
        self.assertIsNone(a['index']['reference']['declared_locator'])

    def test_different_roots_no_dedup(self):
        d = sample(); run = d['sarif']['runs'][0]
        run['originalUriBaseIds'] = {'A': {'uri': 'file:///synthetic/a/'}, 'B': {'uri': 'file:///synthetic/b/'}}
        first = run['results'][0]['locations'][0]
        first['physicalLocation']['artifactLocation'] = {'uri': 'leaf.c', 'uriBaseId': 'A'}
        second = copy.deepcopy(first); second['physicalLocation']['artifactLocation']['uriBaseId'] = 'B'
        run['results'][0]['locations'].append(second)
        rows = model.interpret(d)['runs'][0]['results'][0]['locations']
        self.assertEqual([r['artifact']['direct']['declared_locator'] for r in rows],
                         ['file:///synthetic/a/leaf.c', 'file:///synthetic/b/leaf.c'])
        self.assertEqual([r['location_index'] for r in rows], [0, 1])

    def test_unused_indices_and_cross_run(self):
        for location in ({'uri': 'file:///synthetic/a.c', 'index': 1}, {'uri': 'file:///synthetic/a.c', 'index': True}):
            d = sample(); d['sarif']['runs'][0]['artifacts'] = [{'location': location}]
            self.assertEqual(model.interpret(d)['status'], 'invalid')
        d = sample(); other = copy.deepcopy(d['sarif']['runs'][0])
        d['sarif']['runs'][0]['artifacts'] = [{'location': {'uri': 'file:///synthetic/a.c'}}]
        other['results'][0]['locations'][0]['physicalLocation']['artifactLocation'] = {'index': 0}
        d['sarif']['runs'].append(other)
        self.assertEqual(model.interpret(d)['reasons'][0]['code'], 'index_range')

    def test_base_chain_boundary_and_cycle_precedence(self):
        d = sample(); run = d['sarif']['runs'][0]
        run['originalUriBaseIds'] = {f'B{i}': {'uri': 'x/', 'uriBaseId': f'B{i+1}'} for i in range(7)}
        run['originalUriBaseIds']['B7'] = {'uri': 'file:///synthetic/'}
        physical(d)['artifactLocation'] = {'uri': 'a.c', 'uriBaseId': 'B0'}
        self.assertEqual(model.interpret(d)['status'], 'interpreted')
        run['originalUriBaseIds']['B7'] = {'uri': 'x/', 'uriBaseId': 'B8'}
        run['originalUriBaseIds']['B8'] = {'uri': 'file:///synthetic/'}
        self.assertEqual(model.interpret(d)['reasons'][0]['code'], 'base_depth')
        run['columnKind'] = 'future'
        run['originalUriBaseIds'] = {'X': {'uriBaseId': 'X'}}
        self.assertEqual(model.interpret(d)['reasons'][0]['code'], 'base_cycle')

    def test_locator_length(self):
        d = sample(); run = d['sarif']['runs'][0]
        segment = 'a'*63+'/'
        run['originalUriBaseIds'] = {'A': {'uri': 'file:///synthetic/'+segment*4},
                                     'B': {'uri': segment*4, 'uriBaseId': 'A'}}
        physical(d)['artifactLocation'] = {'uri': 'a.c', 'uriBaseId': 'B'}
        self.assertEqual(model.interpret(d)['reasons'][0]['code'], 'locator_limit')

    def test_uri_subset_and_malformed(self):
        for uri in ('../a', 'a%20.c', 'file:///other/a.c', 'https://example.test/a?x', 'a\\b', 'a/', '//host/a', 'é.c'):
            d = sample(); physical(d)['artifactLocation'] = {'uri': uri}
            self.assertEqual(model.interpret(d)['status'], 'unsupported')
        for uri in ('', 'a\x00.c', 'a\x1b.c', 'a\x85.c', 'a\x9f.c'):
            d = sample(); physical(d)['artifactLocation'] = {'uri': uri}
            self.assertEqual(model.interpret(d)['status'], 'invalid')
        d = sample(); physical(d)['artifactLocation']['uriBaseId'] = 'A'
        self.assertEqual(model.interpret(d)['reasons'][0]['code'], 'absolute_with_base')

    def test_redacted_intermediate_chain_retained(self):
        d = sample(); run = d['sarif']['runs'][0]
        run['originalUriBaseIds'] = {'A': {'uriBaseId': 'B'}, 'B': {'uri': 'file:///synthetic/'}}
        physical(d)['artifactLocation'] = {'uri': 'a.c', 'uriBaseId': 'A'}
        r = model.interpret(d)['runs'][0]['results'][0]['locations'][0]['artifact']['direct']
        self.assertEqual(r['chain'], ['A', 'B'])
        self.assertIsNone(r['declared_locator'])

    def test_redacted_table_uri_retains_chain(self):
        d = sample(); run = d['sarif']['runs'][0]
        run['artifacts'] = [{'location': {'uriBaseId': 'A'}}]
        run['originalUriBaseIds'] = {'A': {'uriBaseId': 'B'}, 'B': {}}
        physical(d)['artifactLocation'] = {'index': 0}
        out = model.interpret(d)
        self.assertEqual(out['status'], 'incomplete')
        r = out['runs'][0]['results'][0]['locations'][0]['artifact']['index']['reference']
        self.assertEqual(r['chain'], ['A', 'B'])
        self.assertIsNone(r['uri'])
        self.assertIsNone(r['declared_locator'])

    def test_unused_base_locator_bound(self):
        d = sample(); run = d['sarif']['runs'][0]
        segment = 'a'*63+'/'
        run['originalUriBaseIds'] = {'A': {'uri': 'file:///synthetic/'+segment*4},
                                     'B': {'uri': segment*4, 'uriBaseId': 'A'}}
        self.assertEqual(model.interpret(d)['reasons'][0]['code'], 'locator_limit')

    def test_global_graph_precedes_earlier_conflict(self):
        d = copy.deepcopy(next(c for c in CASES if c['name'] == 'dual_conflict')['input'])
        other = sample()['sarif']['runs'][0]
        other['originalUriBaseIds'] = {'X': {'uriBaseId': 'X'}}
        d['sarif']['runs'].append(other)
        self.assertEqual(model.interpret(d)['reasons'][0]['code'], 'base_cycle')

    def test_index_with_redacted_direct_modifier(self):
        d = sample(); run = d['sarif']['runs'][0]
        run['artifacts'] = [{'location': {'uri': 'file:///synthetic/a.c'}}]
        physical(d)['artifactLocation'] = {'index': 0, 'uriBaseId': 'MISSING'}
        out = model.interpret(d)
        self.assertEqual(out['status'], 'incomplete')
        a = out['runs'][0]['results'][0]['locations'][0]['artifact']
        self.assertEqual(a['agreement'], 'unknown')
        self.assertEqual(a['direct'], {'pointer': '/sarif/runs/0/results/0/locations/0/physicalLocation/artifactLocation',
                                      'uri': None, 'uri_base_id': 'MISSING', 'chain': ['MISSING'],
                                      'declared_locator': None, 'complete': False})


class RegionsAndBounds(unittest.TestCase):
    def test_late_known_invalid_over_unsupported(self):
        d = sample(); d['sarif']['runs'][0]['columnKind'] = 'future'
        physical(d)['region']['endLine'] = 2
        self.assertEqual(model.interpret(d)['reasons'][0]['code'], 'region_order')
        d = sample(); physical(d)['region'] = {'byteOffset': True}
        self.assertEqual(model.interpret(d)['reasons'][0]['code'], 'integer')
        d = sample(); physical(d)['region'] = {'snippet': {'text': 'synthetic'}}
        self.assertEqual(model.interpret(d)['status'], 'invalid')

    def test_no_mutation_of_input(self):
        d = sample(); prior = copy.deepcopy(d)
        model.interpret(d)
        self.assertEqual(d, prior)

    def test_count_limits(self):
        for key, value in [('artifacts', [{'location': {'uri': 'file:///synthetic/a.c'}}]*129),
                           ('originalUriBaseIds', {f'B{i}': {} for i in range(33)}),
                           ('results', [{'message': {'text': 'x'}, 'locations': []}]*65)]:
            d = sample(); d['sarif']['runs'][0][key] = value
            self.assertEqual(model.interpret(d)['status'], 'invalid')
        d = sample(); d['sarif']['runs'] *= 5
        self.assertEqual(model.interpret(d)['status'], 'invalid')
        d = sample(); d['sarif']['runs'][0]['results'][0]['locations'] *= 5
        self.assertEqual(model.interpret(d)['status'], 'invalid')

    def test_maximum_occurrences_fit_output(self):
        d = sample(); run = d['sarif']['runs'][0]
        loc = run['results'][0]['locations'][0]
        run['results'] = [{'message': {'text': 'x'}, 'locations': [copy.deepcopy(loc) for _ in range(4)]} for _ in range(64)]
        raw = json.dumps(d, separators=(',', ':')).encode()
        self.assertLessEqual(len(raw), 65536)
        out = model.interpret(model.decode(raw))
        self.assertEqual(out['status'], 'interpreted')
        self.assertEqual(sum(len(r['locations']) for r in out['runs'][0]['results']), 256)
        self.assertLessEqual(len(model.serialize(out)), 1048576)
        with self.assertRaises(model.Invalid):
            model.serialize(out, limit=10)

    def test_denied_external_capabilities(self):
        def denied(*_args, **_kwargs):
            raise AssertionError('external capability used')
        with patch('builtins.open', denied), patch.object(socket, 'socket', denied), \
                patch.object(subprocess, 'Popen', denied), patch.object(os, 'system', denied), \
                patch.object(os, 'getenv', denied):
            for case in CASES:
                self.assertEqual(model.interpret(model.decode(json.dumps(case['input']).encode())), case['expected'])
                self.assertIsInstance(model.serialize(case['expected']), bytes)
                output = io.BytesIO()
                status = cli.main([], io.BytesIO(json.dumps(case['input']).encode()), output, io.StringIO())
                self.assertEqual(status, 0 if case['expected']['status'] == 'interpreted' else 2)
                self.assertEqual(json.loads(output.getvalue()), case['expected'])


class Delivery(unittest.TestCase):
    def invoke(self, output, raw=None, args=None):
        errors = io.StringIO()
        result = cli.main([] if args is None else args, io.BytesIO(raw or json.dumps(sample()).encode()), output, errors)
        return result, errors.getvalue()

    def test_normal_and_misuse(self):
        output = io.BytesIO()
        self.assertEqual(self.invoke(output), (0, ''))
        self.assertEqual(json.loads(output.getvalue()), CASES[0]['expected'])
        self.assertEqual(self.invoke(io.BytesIO(), args=['filename'])[0], 2)
        self.assertEqual(self.invoke(io.BytesIO(), args=['--help'])[0], 0)

    def test_short_write(self):
        class Short(io.BytesIO):
            def write(self, payload):
                super().write(payload[:1]); return 1
        self.assertEqual(self.invoke(Short())[0], 3)

    def test_flush_failure(self):
        class Fail(io.BytesIO):
            def flush(self):
                raise OSError('invented')
        self.assertEqual(self.invoke(Fail())[0], 3)
        self.assertEqual(self.invoke(Fail(), args=['--help'])[0], 3)

    def test_broken_pipe(self):
        class Broken(io.BytesIO):
            def write(self, _payload):
                raise BrokenPipeError('invented')
        self.assertEqual(self.invoke(Broken())[0], 3)

    def test_read_failure(self):
        class Fail(io.BytesIO):
            def read(self, _size):
                raise OSError('invented')
        errors = io.StringIO()
        self.assertEqual(cli.main([], Fail(), io.BytesIO(), errors), 3)
        self.assertEqual(errors.getvalue(), 'Input or output operation failed.\n')

    def test_diagnostic_short_writes(self):
        for returned in (1, None, True):
            class Short(io.StringIO):
                def write(self, text):
                    super().write(text[:1])
                    return returned
            errors = Short()
            self.assertEqual(cli.main(['bad'], io.BytesIO(), io.BytesIO(), errors), 3)
            self.assertEqual(errors.getvalue(), 'U')

    def test_diagnostic_flush_and_write_failures(self):
        class Flush(io.StringIO):
            def flush(self):
                raise OSError('invented')
        class Broken(io.StringIO):
            def write(self, _text):
                raise BrokenPipeError('invented')
        for errors in (Flush(), Broken()):
            self.assertEqual(cli.main(['bad'], io.BytesIO(), io.BytesIO(), errors), 3)
            self.assertFalse(cli.diagnostic(errors, 'fixed\n'))

    def test_actual_closed_stderr_barrier_normal_and_optimized(self):
        # Parent closes sinks before releasing one-byte barrier: no race with main.
        wrapper = (
            'import runpy,sys; '
            'sys.stdin.buffer.read(1); '
            'path=sys.argv[1]; sys.path.insert(0,sys.argv[2]); '
            'sys.argv=[path]+sys.argv[3:]; runpy.run_path(path,run_name="__main__")'
        )
        scenarios = [(['--bad-synthetic-argument'], False, 3),
                     (['--bad-synthetic-argument'], True, 3),
                     (['--help'], True, 3), ([], True, 3), ([], False, 0)]
        for flags in ([], ['-O']):
            for args, close_output, expected in scenarios:
                with self.subTest(flags=flags, args=args, close_output=close_output):
                    child = subprocess.Popen([sys.executable, *flags, '-c', wrapper,
                                              str(ROOT/'cli.py'), str(ROOT), *args],
                                             stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)
                    child.stderr.close(); child.stderr = None
                    if close_output:
                        child.stdout.close(); child.stdout = None
                    raw = b'!'+(json.dumps(sample()).encode() if not args else b'')
                    try:
                        output, _ = child.communicate(input=raw, timeout=10)
                    except subprocess.TimeoutExpired:
                        child.kill(); child.communicate(timeout=10)
                        raise
                    self.assertEqual(child.returncode, expected)
                    if args and not close_output:
                        self.assertEqual(output, b'')
                    elif expected == 0:
                        self.assertEqual(json.loads(output), CASES[0]['expected'])

    def test_actual_cli_optimized_and_escape(self):
        d = sample(); d['sarif']['runs'][0]['tool']['driver']['name'] = 'invented\x1b'
        for flags in ([], ['-O']):
            run = subprocess.run([sys.executable, *flags, str(ROOT/'cli.py')], input=json.dumps(d).encode(),
                                 capture_output=True, timeout=10, check=False)
            self.assertEqual(run.returncode, 0)
            self.assertNotIn(b'\x1b', run.stdout)
            self.assertTrue(run.stdout.isascii())
        run = subprocess.run([sys.executable, str(ROOT/'cli.py'), 'file'], capture_output=True, timeout=10, check=False)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(run.stdout, b'')

    def test_actual_closed_pipe_and_help(self):
        for args, expected in [([], 'Input or output operation failed.'), (['--help'], 'Output delivery failed.')]:
            child = subprocess.Popen([sys.executable, str(ROOT/'cli.py'), *args],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            child.stdout.close(); child.stdout = None
            if not args:
                child.stdin.write(json.dumps(sample()).encode())
            child.stdin.close(); child.stdin = None
            try:
                _, error = child.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill(); child.communicate(timeout=10)
                raise
            self.assertEqual(child.returncode, 3)
            self.assertIn(error, ((expected+'\n').encode(), (expected+'\r\n').encode()))


if __name__ == '__main__':
    unittest.main()
