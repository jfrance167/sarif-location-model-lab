# Frozen contract v1

Frozen October 5, 2026 before model/CLI implementation. PLAN and its 03:06
approval supply the scope. tests/oracles.json is hand-authored independently;
implementation may not regenerate its expectations. Contract changes require
an explicit decision and new oracle receipt, never silently matching code.

## Admission and field shapes

Exact built-in dict/list/str/int/bool/None only; no custom objects, shared cycles,
floats, surrogate characters, duplicate JSON keys, BOM or nonfinite numbers.
Integers are 0..2147483647; all present region line/column integers are positive.
64 KiB UTF-8 input, nesting depth 16 (root depth 1), 4096 value nodes plus keys,
1024 Unicode characters/string, 10 numeric-token characters, 512 URI/derived
locator characters, 64 label characters. Four runs, 128 artifacts/run,
32 bases/run, 64 total results, four locations/result, eight base entries/chain.
API admission applies equivalent serialized-input bounds. Output ASCII compact
JSON plus newline is serialized in full and capped at 1 MiB before delivery.

Envelope requires schema_version (exact int 1), profile (string), sarif (object).
Unknown bounded version/profile strings or schema integers are unsupported.
Known structure is still validated before unsupported status. sarif requires
version string and runs array (null runs is unsupported); optional $schema string
is inert. Run requires tool.driver.name string; columnKind is optional string;
artifacts defaults [], originalUriBaseIds defaults {}, results missing/null is
incomplete. Tool/driver objects only admit driver/name respectively. Each artifact
requires location object; base values are artifact-location objects without index.
Result requires message.text string, optional ruleId string, optional locations
array (null locations is invalid). Location requires physicalLocation object,
which requires artifactLocation object and optionally region object.
Unknown fields at every object level are unsupported. All known fields are
validated even behind unknown fields, unsupported kinds, or unused declarations.

Artifact-location known fields: uri string, uriBaseId string with exact base-ID
grammar, index exact integer (forbidden in bases). Table entry index, if supplied,
must match slot. Physical references require uri or index; table locations require
uri or uriBaseId. Base entries may be empty/redacted, or only uriBaseId. Leaf
URI strings require nonempty final path segment. Base URI strings require final
slash; wrong directory shape is unsupported. Prefixes/segment/base-ID grammar
and absolute-plus-base invalidity are defined in PLAN. Empty URI/control URI is
invalid; other non-profile forms unsupported. Every supplied index must be
in range in its own run, even unused. Missing graph targets are incomplete;
cycles and chains longer than eight are invalid globally.

Region known fields: startLine/startColumn/endLine/endColumn positive int;
byteOffset/byteLength/charOffset/charLength nonnegative int (unsupported feature).
If text fields exist, or no offset fields exist, startLine is required and explicit
run columnKind is required. Supported kinds: utf16CodeUnits, unicodeCodePoints.
Other bounded strings unsupported. endLine defaults startLine, startColumn 1;
endColumn missing means unknown numeric end-of-line, incomplete. Reversed
lines or same-line columns invalid; equal columns admitted insertion point.
No source content inspection or unit conversion.

## Validation, output and aggregation

Order: common bounded admission; structural and known declaration validation
in input run/result/location order (including table/bases); global base graph;
dual-reference conflicts; first unsupported feature; complete interpretation.
An invalid anywhere dominates unsupported, which dominates incomplete, which
dominates interpreted. Error reports release zero runs, never partial rows.
Errors contain one fixed code/pointer, no target text. Generic admission errors
use pointer empty. Unknown field pointers escape ~ and / as JSON Pointer tokens.

Report exact keys: schema_version=1, status, reasons, runs. reason keys: code,
pointer. Successful/incomplete run keys: run_index, results_state, results;
states supplied/not_supplied. Result keys: result_index, locations_state,
locations; locations state supplied/not_supplied. Every occurrence retained.
Missing locations and supplied [] both produce reason locations_not_supplied
and incomplete (state still distinguishes absent from supplied). Missing/null
results produce results_not_supplied and no results. Empty supplied results or
runs are interpreted empty metadata and carry no clean-scan meaning.

Location keys: location_index, artifact, region. Artifact keys: direct, index,
agreement; direct is null or reference; index is null or {artifact_index,reference}.
Agreement: single_declaration, declared_locator_match, unknown; conflict invalid.
Reference keys: pointer, uri (null if absent), uri_base_id (null if absent),
chain (ordered IDs leaf toward root), declared_locator (null if incomplete),
complete bool. Missing/redacted bases and unbased relative paths retain symbolic
chain, never fabricated root. A complete reference concatenates supported
directory text only. Both references must be complete before text comparison.

Region absent: {state:not_supplied}; reason region_not_supplied. Region supplied:
{state:supplied,column_kind,start_line,start_column,end_line,end_column,
defaulted:[startColumn and/or endLine in that order],end_bound:exclusive|unknown_end_of_line}.
Incomplete reasons in row order: locator_incomplete, then region_not_supplied
or end_column_unknown. Pointer for locator reason is artifactLocation, for
region reasons region pointer. Missing locations points to locations even absent.

Fixed invalid codes: admission, shape, integer, label, uri, base_id,
absolute_with_base, index_range, self_index, base_index, missing_reference,
base_cycle, base_depth, locator_limit, column_kind_missing, region_order,
reference_conflict.
Unsupported codes: schema_version, profile, version, runs_null, unknown_field,
uri_profile, column_kind, offset_region. First encountered unsupported recorded,
but known invalid overrides it. Decoder failures use admission. Resource limits
use admission except chain/derived locator limits above.

CLI: no args stdin binary -> stdout binary only; --help emits a fixed ASCII
usage and succeeds only on complete delivery. Misuse exit 2 fixed stderr.
interpreted exit 0; every other report status exit 2. Read/serialization/output
failure exit 3 fixed stderr, including short writes/flush/broken pipe. Physical
partial stdout cannot be rolled back. No atomic-output guarantee. Pure model
imports json/re only; no artifact I/O, paths, URLs, environment or subprocess.
