"""One-time independent fixture authoring. No application imports or semantics.

Literal coordinates and locator expectations were selected from CONTRACT.md.
Run from the project root; exclusive creation preserves previously frozen data.
"""
import copy
import json
from pathlib import Path


def document(location=None, *, kind='utf16CodeUnits', artifacts=None, bases=None):
    run = {'tool': {'driver': {'name': 'synthetic'}}, 'columnKind': kind,
           'results': [{'message': {'text': 'invented'}, 'locations': [
               {'physicalLocation': location or {
                   'artifactLocation': {'uri': 'file:///synthetic/a.c'},
                   'region': {'startLine': 3, 'endColumn': 5}}}]}]}
    if artifacts is not None:
        run['artifacts'] = artifacts
    if bases is not None:
        run['originalUriBaseIds'] = bases
    return {'schema_version': 1, 'profile': 'sarif-locations-v1',
            'sarif': {'version': '2.1.0', 'runs': [run]}}


P = '/sarif/runs/0/results/0/locations/0/physicalLocation'


def ref(uri='file:///synthetic/a.c', base=None, chain=None, locator='file:///synthetic/a.c', pointer=P+'/artifactLocation'):
    return {'pointer': pointer, 'uri': uri, 'uri_base_id': base,
            'chain': chain or [], 'declared_locator': locator,
            'complete': locator is not None}


def row(direct=None, index=None, agreement='single_declaration', region=None):
    return {'location_index': 0, 'artifact': {'direct': direct, 'index': index,
            'agreement': agreement}, 'region': region or {
                'state': 'supplied', 'column_kind': 'utf16CodeUnits',
                'start_line': 3, 'start_column': 1, 'end_line': 3,
                'end_column': 5, 'defaulted': ['startColumn', 'endLine'],
                'end_bound': 'exclusive'}}


def report(rows, reasons=None, status='interpreted', results_state='supplied', locations_state='supplied'):
    return {'schema_version': 1, 'status': status, 'reasons': reasons or [],
            'runs': [{'run_index': 0, 'results_state': results_state,
                      'results': [{'result_index': 0, 'locations_state': locations_state,
                                   'locations': rows}]}]}


def reason(code, pointer):
    return {'code': code, 'pointer': pointer}


cases = []


def add(name, source, expected):
    cases.append({'name': name, 'input': source, 'expected': expected})


def error(name, source, code, pointer, status='invalid'):
    add(name, source, {'schema_version': 1, 'status': status,
                      'reasons': [reason(code, pointer)], 'runs': []})


add('absolute', document(), report([row(ref())]))
bases = {'ROOT': {'uri': 'file:///synthetic/project/'},
         'SRC': {'uri': 'src/', 'uriBaseId': 'ROOT'}}
add('directory_chain', document({'artifactLocation': {'uri': 'a.c', 'uriBaseId': 'SRC'},
                                'region': {'startLine': 3, 'endColumn': 5}}, bases=bases),
    report([row(ref('a.c', 'SRC', ['SRC', 'ROOT'], 'file:///synthetic/project/src/a.c'))]))
table = [{'location': {'uri': 'file:///synthetic/a.c'}}]
table_ref = ref(pointer='/sarif/runs/0/artifacts/0/location')
add('matching_dual', document({'artifactLocation': {'uri': 'file:///synthetic/a.c', 'index': 0},
                              'region': {'startLine': 3, 'endColumn': 5}}, artifacts=table),
    report([row(ref(), {'artifact_index': 0, 'reference': table_ref}, 'declared_locator_match')]))
for value, code, name in [(1, 'index_range', 'index_out_of_range'), (True, 'integer', 'bool_index')]:
    error(name, document({'artifactLocation': {'index': value}, 'region': {'startLine': 3, 'endColumn': 5}}, artifacts=table),
          code, P+'/artifactLocation/index')
error('dual_conflict', document({'artifactLocation': {'uri': 'file:///synthetic/b.c', 'index': 0},
                                'region': {'startLine': 3, 'endColumn': 5}}, artifacts=table),
      'reference_conflict', P+'/artifactLocation')
for name, graph, chain in [('missing_base', {}, ['ROOT']), ('redacted_base', {'ROOT': {}}, ['ROOT'])]:
    add(name, document({'artifactLocation': {'uri': 'a.c', 'uriBaseId': 'ROOT'},
                        'region': {'startLine': 3, 'endColumn': 5}}, bases=graph),
        report([row(ref('a.c', 'ROOT', chain, None))],
               [reason('locator_incomplete', P+'/artifactLocation')], 'incomplete'))
error('unused_cycle', document(bases={'A': {'uri': 'a/', 'uriBaseId': 'B'},
                                     'B': {'uri': 'b/', 'uriBaseId': 'A'}}),
      'base_cycle', '/sarif/runs/0/originalUriBaseIds/A')
r = row(ref()); r['region'].update(end_column=None, end_bound='unknown_end_of_line')
add('unknown_end', document({'artifactLocation': {'uri': 'file:///synthetic/a.c'},
                            'region': {'startLine': 3}}),
    report([r], [reason('end_column_unknown', P+'/region')], 'incomplete'))
r = row(ref()); r['region'].update(start_column=4, end_column=4, defaulted=['endLine'])
add('insertion_point', document({'artifactLocation': {'uri': 'file:///synthetic/a.c'},
                                'region': {'startLine': 3, 'startColumn': 4, 'endColumn': 4}}), report([r]))
error('reversed_columns', document({'artifactLocation': {'uri': 'file:///synthetic/a.c'},
                                   'region': {'startLine': 3, 'startColumn': 4, 'endColumn': 3}}),
      'region_order', P+'/region')
r = row(ref()); r['region']['column_kind'] = 'unicodeCodePoints'
add('codepoint_units', document(kind='unicodeCodePoints'), report([r]))
d = document(); del d['sarif']['runs'][0]['columnKind']
error('missing_units', d, 'column_kind_missing', '/sarif/runs/0/columnKind')
error('unknown_units', document(kind='bytes'), 'column_kind', '/sarif/runs/0/columnKind', 'unsupported')
error('wrong_units_type', document(kind=4), 'shape', '/sarif/runs/0/columnKind')
error('byte_region', document({'artifactLocation': {'uri': 'file:///synthetic/a.c'}, 'region': {'byteOffset': 0, 'byteLength': 1}}),
      'offset_region', P+'/region', 'unsupported')
error('percent_leaf', document({'artifactLocation': {'uri': 'file:///synthetic/a%20.c'}, 'region': {'startLine': 3, 'endColumn': 5}}),
      'uri_profile', P+'/artifactLocation/uri', 'unsupported')
error('base_without_slash', document(bases={'ROOT': {'uri': 'file:///synthetic/project'}}),
      'uri_profile', '/sarif/runs/0/originalUriBaseIds/ROOT/uri', 'unsupported')
add('no_region', document({'artifactLocation': {'uri': 'file:///synthetic/a.c'}}),
    report([row(ref(), region={'state': 'not_supplied'})], [reason('region_not_supplied', P+'/region')], 'incomplete'))
for name, supplied in [('absent_locations', False), ('empty_locations', True)]:
    d = document(); result = d['sarif']['runs'][0]['results'][0]
    if supplied:
        result['locations'] = []
    else:
        del result['locations']
    add(name, d, report([], [reason('locations_not_supplied', '/sarif/runs/0/results/0/locations')],
                        'incomplete', locations_state='supplied' if supplied else 'not_supplied'))
for name, value in [('null_results', None), ('empty_results', [])]:
    d = document(); d['sarif']['runs'][0]['results'] = value
    add(name, d, {'schema_version': 1, 'status': 'incomplete' if value is None else 'interpreted',
                 'reasons': [reason('results_not_supplied', '/sarif/runs/0/results')] if value is None else [],
                 'runs': [{'run_index': 0, 'results_state': 'not_supplied' if value is None else 'supplied', 'results': []}]})
d = document(); d['sarif']['runs'][0]['results'].append({'message': {'text': 7}})
error('late_malformed', d, 'shape', '/sarif/runs/0/results/1/message/text')
d = document(); d['sarif']['extra'] = True; d['sarif']['runs'][0]['artifacts'] = [{'location': {'index': True}}]
error('unused_invalid_over_unknown', d, 'integer', '/sarif/runs/0/artifacts/0/location/index')
d = document(); d['sarif']['runs'][0]['results'].append(copy.deepcopy(d['sarif']['runs'][0]['results'][0]))
expected = report([row(ref())]); second = copy.deepcopy(expected['runs'][0]['results'][0]); second['result_index'] = 1
second['locations'][0]['artifact']['direct']['pointer'] = '/sarif/runs/0/results/1/locations/0/physicalLocation/artifactLocation'
expected['runs'][0]['results'].append(second)
add('duplicate_occurrences', d, expected)
Path('tests').mkdir(exist_ok=True)
with Path('tests/oracles.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(cases, stream, ensure_ascii=True, indent=2)
    stream.write('\n')
