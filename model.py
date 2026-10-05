"""Bounded synthetic SARIF metadata interpretation; never opens artifacts.

Public interpret() accepts exact built-in JSON data. decode() also enforces raw
token/byte bounds. This is the restricted CONTRACT.md profile, not a SARIF
validator or an artifact identity/defect assessment.
"""
import json
import re

MAX_INPUT = 65536
MAX_OUTPUT = 1048576
KINDS = ('utf16CodeUnits', 'unicodeCodePoints')
SEGMENT = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z')
BASE_ID = re.compile(r'[A-Za-z_][A-Za-z0-9_-]{0,31}\Z')
ROOTS = ('file:///synthetic/', 'https://example.test/')


class Invalid(ValueError):
    """Fixed report code and inert input pointer, never an input excerpt."""

    def __init__(self, code, pointer=''):
        super().__init__(code)
        self.code = code
        self.pointer = pointer


def pointer(parent, key):
    return parent + '/' + str(key).replace('~', '~0').replace('/', '~1')


def _admit(value):
    nodes = 0
    active = set()

    def visit(item, depth):
        nonlocal nodes
        nodes += 1
        if depth > 16 or nodes > 4096:
            raise Invalid('admission')
        kind = type(item)
        if kind is str:
            if len(item) > 1024 or any(0xD800 <= ord(c) <= 0xDFFF for c in item):
                raise Invalid('admission')
        elif kind is int:
            if not 0 <= item <= 2147483647:
                raise Invalid('admission')
        elif item is None or kind is bool:
            return
        elif kind in (list, dict):
            if id(item) in active:
                raise Invalid('admission')
            active.add(id(item))
            if kind is dict:
                for key, child in item.items():
                    if type(key) is not str:
                        raise Invalid('admission')
                    visit(key, depth + 1)
                    visit(child, depth + 1)
            else:
                for child in item:
                    visit(child, depth + 1)
            active.remove(id(item))
        else:
            raise Invalid('admission')

    visit(value, 1)
    if len(json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')) > MAX_INPUT:
        raise Invalid('admission')


def decode(raw):
    """Decode bytes with bounded nesting before recursive JSON parsing."""
    if type(raw) is not bytes or len(raw) > MAX_INPUT or raw.startswith(b'\xef\xbb\xbf'):
        raise Invalid('admission')
    try:
        text = raw.decode('utf-8', errors='strict')
        # Ignore brackets inside strings; JSON parser handles syntax afterward.
        depth = 0
        quoted = escaped = False
        for char in text:
            if quoted:
                if escaped:
                    escaped = False
                elif char == '\\':
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in '[{':
                depth += 1
                if depth > 16:
                    raise Invalid('admission')
            elif char in ']}':
                depth -= 1

        def integer(token):
            if len(token) > 10:
                raise Invalid('admission')
            return int(token)

        def forbidden(_token):
            raise Invalid('admission')

        def pairs(entries):
            result = {}
            for key, child in entries:
                if key in result:
                    raise Invalid('admission')
                result[key] = child
            return result

        value = json.loads(text, parse_int=integer, parse_float=forbidden,
                           parse_constant=forbidden, object_pairs_hook=pairs)
        _admit(value)
        return value
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise Invalid('admission') from error


def failure(code, where='', status='invalid'):
    return {'schema_version': 1, 'status': status,
            'reasons': [{'code': code, 'pointer': where}], 'runs': []}


class Validator:
    """Known validation continues after encountering an unsupported feature."""

    def __init__(self):
        self.unsupported = []
        self.result_count = 0

    def unknown(self, code, where):
        self.unsupported.append((code, where))

    def obj(self, value, where, allowed, required=()):
        if type(value) is not dict:
            raise Invalid('shape', where)
        for key in required:
            if key not in value:
                raise Invalid('shape', pointer(where, key))
        for key in value:
            if key not in allowed:
                self.unknown('unknown_field', pointer(where, key))
        return value

    def string(self, value, where, label=False):
        if type(value) is not str:
            raise Invalid('shape', where)
        if label and len(value) > 64:
            raise Invalid('label', where)

    def integer(self, value, where, positive=False):
        if type(value) is not int or value < (1 if positive else 0):
            raise Invalid('integer', where)

    def array(self, value, where, maximum):
        if type(value) is not list:
            raise Invalid('shape', where)
        if len(value) > maximum:
            raise Invalid('admission')

    def uri_supported(self, uri, directory=False):
        remainder = uri
        for root in ROOTS:
            if uri.startswith(root):
                remainder = uri[len(root):]
                break
        else:
            if ':' in uri or uri.startswith('/'):
                return False
        if directory:
            if not uri.endswith('/'):
                return False
            remainder = remainder[:-1] if remainder.endswith('/') else remainder
            if not remainder:
                return any(uri == root for root in ROOTS)
        elif uri.endswith('/') or not remainder:
            return False
        return all(SEGMENT.fullmatch(s) and s not in ('.', '..') for s in remainder.split('/'))

    def artifact(self, value, where, table_count, base=False, slot=None):
        self.obj(value, where, ('uri', 'uriBaseId', 'index'))
        if 'index' in value:
            at = pointer(where, 'index')
            self.integer(value['index'], at)
            if base:
                raise Invalid('base_index', at)
            # Mutation seam: range failure must stay a report, not IndexError.
            if value['index'] >= table_count:
                raise Invalid('index_range', at)
            if slot is not None and value['index'] != slot:
                raise Invalid('self_index', at)
        if 'uri' in value:
            at = pointer(where, 'uri')
            self.string(value['uri'], at)
            uri = value['uri']
            if not uri or len(uri) > 512 or any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in uri):
                raise Invalid('uri', at)
            if not self.uri_supported(uri, directory=base):
                self.unknown('uri_profile', at)
            if any(uri.startswith(root) for root in ROOTS) and 'uriBaseId' in value:
                raise Invalid('absolute_with_base', where)
        if 'uriBaseId' in value:
            at = pointer(where, 'uriBaseId')
            self.string(value['uriBaseId'], at)
            if not BASE_ID.fullmatch(value['uriBaseId']):
                raise Invalid('base_id', at)
        if not base:
            supplied = ('uri', 'uriBaseId') if slot is not None else ('uri', 'index')
            if not any(key in value for key in supplied):
                raise Invalid('missing_reference', where)

    def region(self, value, where, run, run_at):
        text = ('startLine', 'startColumn', 'endLine', 'endColumn')
        offsets = ('byteOffset', 'byteLength', 'charOffset', 'charLength')
        self.obj(value, where, text + offsets)
        for key in text + offsets:
            if key in value:
                self.integer(value[key], pointer(where, key), positive=key in text)
        if any(key in value for key in offsets):
            self.unknown('offset_region', where)
        is_text = any(key in value for key in text) or not any(key in value for key in offsets)
        if is_text:
            if 'startLine' not in value:
                raise Invalid('shape', pointer(where, 'startLine'))
            if 'columnKind' not in run:
                raise Invalid('column_kind_missing', pointer(run_at, 'columnKind'))
            start_line = value['startLine']
            end_line = value.get('endLine', start_line)
            if end_line < start_line or (end_line == start_line and
                                        value.get('endColumn', 2147483647) < value.get('startColumn', 1)):
                raise Invalid('region_order', where)

    def graph(self, bases, where):
        # Validate every chain, including unused and partially redacted entries.
        for origin in bases:
            current = origin
            chain = []
            while current is not None:
                if current in chain:
                    raise Invalid('base_cycle', pointer(where, origin))
                chain.append(current)
                if len(chain) > 8:
                    raise Invalid('base_depth', pointer(where, origin))
                if current not in bases:
                    break
                current = bases[current].get('uriBaseId')

    def validate(self, value):
        self.obj(value, '', ('schema_version', 'profile', 'sarif'), ('schema_version', 'profile', 'sarif'))
        self.integer(value['schema_version'], '/schema_version')
        if value['schema_version'] != 1:
            self.unknown('schema_version', '/schema_version')
        self.string(value['profile'], '/profile', label=True)
        if value['profile'] != 'sarif-locations-v1':
            self.unknown('profile', '/profile')
        sarif = self.obj(value['sarif'], '/sarif', ('version', '$schema', 'runs'), ('version', 'runs'))
        self.string(sarif['version'], '/sarif/version', label=True)
        if sarif['version'] != '2.1.0':
            self.unknown('version', '/sarif/version')
        if '$schema' in sarif:
            self.string(sarif['$schema'], '/sarif/$schema')
        if sarif['runs'] is None:
            self.unknown('runs_null', '/sarif/runs')
            return
        self.array(sarif['runs'], '/sarif/runs', 4)
        for run_index, run in enumerate(sarif['runs']):
            at = '/sarif/runs/' + str(run_index)
            self.run(run, at)
        # All structural validation precedes global graph/reference checks.
        for run_index, run in enumerate(sarif['runs']):
            at = '/sarif/runs/' + str(run_index)
            self.graph(run.get('originalUriBaseIds', {}), at + '/originalUriBaseIds')
        for run_index, run in enumerate(sarif['runs']):
            at = '/sarif/runs/' + str(run_index)
            # Resolve all declarations to enforce derived bounds, even unused.
            for name, base in run.get('originalUriBaseIds', {}).items():
                reference(base, pointer(at+'/originalUriBaseIds', name), run, directory=True)
            for slot, artifact in enumerate(run.get('artifacts', [])):
                reference(artifact['location'], at+'/artifacts/'+str(slot)+'/location', run)
            for result_index, result in enumerate(run.get('results') or []):
                for location_index, location in enumerate(result.get('locations', [])):
                    here = at+'/results/'+str(result_index)+'/locations/'+str(location_index)+'/physicalLocation/artifactLocation'
                    artifact_projection(location['physicalLocation']['artifactLocation'], here, run)

    def run(self, run, at):
        self.obj(run, at, ('tool', 'columnKind', 'artifacts', 'originalUriBaseIds', 'results'), ('tool',))
        tool = self.obj(run['tool'], at+'/tool', ('driver',), ('driver',))
        driver = self.obj(tool['driver'], at+'/tool/driver', ('name',), ('name',))
        self.string(driver['name'], at+'/tool/driver/name', label=True)
        if 'columnKind' in run:
            self.string(run['columnKind'], at+'/columnKind', label=True)
            if run['columnKind'] not in KINDS:
                self.unknown('column_kind', at+'/columnKind')
        artifacts = run.get('artifacts', [])
        self.array(artifacts, at+'/artifacts', 128)
        for slot, artifact in enumerate(artifacts):
            here = at+'/artifacts/'+str(slot)
            self.obj(artifact, here, ('location',), ('location',))
            self.artifact(artifact['location'], here+'/location', len(artifacts), slot=slot)
        bases = self.obj(run.get('originalUriBaseIds', {}), at+'/originalUriBaseIds',
                         run.get('originalUriBaseIds', {}).keys() if type(run.get('originalUriBaseIds', {})) is dict else ())
        if len(bases) > 32:
            raise Invalid('admission')
        for name, base in bases.items():
            here = pointer(at+'/originalUriBaseIds', name)
            if not BASE_ID.fullmatch(name):
                raise Invalid('base_id', here)
            self.artifact(base, here, len(artifacts), base=True)
        results = run.get('results')
        if results is None:
            return
        self.array(results, at+'/results', 64)
        self.result_count += len(results)
        if self.result_count > 64:
            raise Invalid('admission')
        for result_index, result in enumerate(results):
            here = at+'/results/'+str(result_index)
            self.obj(result, here, ('ruleId', 'message', 'locations'), ('message',))
            message = self.obj(result['message'], here+'/message', ('text',), ('text',))
            self.string(message['text'], here+'/message/text')
            if 'ruleId' in result:
                self.string(result['ruleId'], here+'/ruleId', label=True)
            locations = result.get('locations', [])
            self.array(locations, here+'/locations', 4)
            for location_index, location in enumerate(locations):
                loc_at = here+'/locations/'+str(location_index)
                self.obj(location, loc_at, ('physicalLocation',), ('physicalLocation',))
                physical = self.obj(location['physicalLocation'], loc_at+'/physicalLocation',
                                    ('artifactLocation', 'region'), ('artifactLocation',))
                self.artifact(physical['artifactLocation'], loc_at+'/physicalLocation/artifactLocation', len(artifacts))
                if 'region' in physical:
                    self.region(physical['region'], loc_at+'/physicalLocation/region', run, at)


def reference(location, where, run, directory=False):
    """Return symbolic provenance; concatenate only fully declared chains."""
    uri = location.get('uri')
    base_id = location.get('uriBaseId')
    result = {'pointer': where, 'uri': uri, 'uri_base_id': base_id,
              'chain': [], 'declared_locator': None, 'complete': False}
    check = Validator()
    if uri is None:
        current = base_id
        bases = run.get('originalUriBaseIds', {})
        while current is not None and current not in result['chain'] and len(result['chain']) < 8:
            result['chain'].append(current)
            current = bases.get(current, {}).get('uriBaseId')
        return result
    if not check.uri_supported(uri, directory=directory):
        return result
    if any(uri.startswith(root) for root in ROOTS):
        result.update(declared_locator=uri, complete=True)
        return result
    parts = [uri]
    current = base_id
    bases = run.get('originalUriBaseIds', {})
    while current is not None:
        if current in result['chain'] or len(result['chain']) >= 8:
            # Graph validation already produces a precise global reason.
            return result
        result['chain'].append(current)
        entry = bases.get(current)
        if entry is None:
            return result
        base_uri = entry.get('uri')
        if base_uri is None or not check.uri_supported(base_uri, directory=True):
            # Retain the rest of an incomplete symbolic chain, without guessing.
            current = entry.get('uriBaseId')
            while current is not None and current not in result['chain'] and len(result['chain']) < 8:
                result['chain'].append(current)
                current = bases.get(current, {}).get('uriBaseId')
            return result
        parts.append(base_uri)
        if any(base_uri.startswith(root) for root in ROOTS):
            locator = ''.join(reversed(parts))
            if len(locator) > 512:
                raise Invalid('locator_limit', where)
            result.update(declared_locator=locator, complete=True)
            return result
        current = entry.get('uriBaseId')
    return result


def artifact_projection(location, where, run):
    direct = reference(location, where, run) if 'uri' in location or 'uriBaseId' in location else None
    indexed = None
    if 'index' in location:
        index = location['index']
        table = run.get('artifacts', [])
        # A defensive boundary keeps range-check mutations from becoming crashes.
        if index < len(table):
            at = where.split('/results/')[0]+'/artifacts/'+str(index)+'/location'
            indexed = {'artifact_index': index, 'reference': reference(table[index]['location'], at, run)}
    agreement = 'single_declaration'
    if direct is not None and indexed is not None:
        if direct['complete'] and indexed['reference']['complete']:
            if direct['declared_locator'] != indexed['reference']['declared_locator']:
                raise Invalid('reference_conflict', where)
            agreement = 'declared_locator_match'
        else:
            agreement = 'unknown'
    return {'direct': direct, 'index': indexed, 'agreement': agreement}


def region_projection(region, kind):
    if region is None:
        return {'state': 'not_supplied'}
    return {'state': 'supplied', 'column_kind': kind,
            'start_line': region['startLine'], 'start_column': region.get('startColumn', 1),
            'end_line': region.get('endLine', region['startLine']),
            'end_column': region.get('endColumn'),
            'defaulted': [key for key in ('startColumn', 'endLine') if key not in region],
            'end_bound': 'exclusive' if 'endColumn' in region else 'unknown_end_of_line'}


def interpret(value):
    """Return a complete bounded inert report, or zero rows on rejection."""
    try:
        _admit(value)
        validator = Validator()
        validator.validate(value)
        if validator.unsupported:
            code, at = validator.unsupported[0]
            return failure(code, at, 'unsupported')
        report = {'schema_version': 1, 'status': 'interpreted', 'reasons': [], 'runs': []}

        def incomplete(code, at):
            report['status'] = 'incomplete'
            report['reasons'].append({'code': code, 'pointer': at})

        for run_index, run in enumerate(value['sarif']['runs']):
            at = '/sarif/runs/'+str(run_index)
            results = run.get('results')
            projected = {'run_index': run_index, 'results_state': 'not_supplied' if results is None else 'supplied', 'results': []}
            report['runs'].append(projected)
            if results is None:
                incomplete('results_not_supplied', at+'/results')
                continue
            for result_index, result in enumerate(results):
                here = at+'/results/'+str(result_index)
                locations = result.get('locations', [])
                out = {'result_index': result_index, 'locations_state': 'supplied' if 'locations' in result else 'not_supplied', 'locations': []}
                projected['results'].append(out)
                if not locations:
                    incomplete('locations_not_supplied', here+'/locations')
                for location_index, location in enumerate(locations):
                    loc_at = here+'/locations/'+str(location_index)+'/physicalLocation'
                    physical = location['physicalLocation']
                    artifact = artifact_projection(physical['artifactLocation'], loc_at+'/artifactLocation', run)
                    references = [artifact['direct']]
                    if artifact['index'] is not None:
                        references.append(artifact['index']['reference'])
                    if any(ref is not None and not ref['complete'] for ref in references):
                        incomplete('locator_incomplete', loc_at+'/artifactLocation')
                    region = region_projection(physical.get('region'), run.get('columnKind'))
                    if region['state'] == 'not_supplied':
                        incomplete('region_not_supplied', loc_at+'/region')
                    elif region['end_bound'] == 'unknown_end_of_line':
                        incomplete('end_column_unknown', loc_at+'/region')
                    out['locations'].append({'location_index': location_index, 'artifact': artifact, 'region': region})
        serialize(report)
        return report
    except Invalid as error:
        return failure(error.code, error.pointer)


def serialize(report, limit=MAX_OUTPUT):
    """Serialize completely before delivery; no transactional stdout promise."""
    payload = (json.dumps(report, ensure_ascii=True, separators=(',', ':'))+'\n').encode('ascii')
    if len(payload) > limit:
        raise Invalid('admission')
    return payload
