# SARIF Location Model Lab: proposed plan

October 5, 2026. **Stages 1–3 approved at 03:06; recovered at 03:26.** Sole writer:
this existing chat. Authority: coordinator's 02:41 research decision and 03:06
implementation approval in `.private/coordination/2026-10-05/SUCCESSORS.md`.
Earlier Keyless closeout remains separately
accepted with 58 unsuppressed Bandit advisories, fresh-restore/vboxguest/manual
hostile-use gates. This project does not alter the scanner or VM.

## Problem and success

Build a small offline teaching CLI that explains supplied synthetic SARIF
location declarations without finding/opening the referenced artifact. Show
reference provenance, base-chain text, coordinate defaults and unknown bounds.
Same locator text is not same file/content, same diagnostic or same root cause.
Success: independently specified cases give exact expected metadata projections,
unknowns and rejection labels; hostile-sized or malformed input stays bounded
and inert. Standard-library Python 3.12+, portable Windows/Linux model, no
additional dependencies or inference runtime. See RESEARCH.md for alternatives,
actual source/test/CI/license review and the original-build recommendation.

## Proposed supported profile

Stdin UTF-8 JSON only -> one inert ASCII JSON report on stdout. No filename
parameter, artifact/source read, glob, environment substitution, URL/schema
lookup, network, subprocess, package install, credentials, scanner adapter,
VM operation or output-directory management. Synthetic fixtures will be authored
independently after approval; no real/private SARIF import.

Envelope: exact `schema_version: 1`, `profile: "sarif-locations-v1"`, and `sarif`.
SARIF subset: version `2.1.0`; optional inert `$schema`; array `runs`; each run
has `tool.driver.name`, optional `columnKind`, `artifacts`, `originalUriBaseIds`
and `results`. Results admit optional ruleId, required message.text (bounded,
not interpreted), and zero-to-four locations. A supported location contains
physicalLocation.artifactLocation and optional region. Tool/rule names are labels,
not authenticated identities. Full SARIF validation is explicitly out of scope.

Supported URI text grammar is deliberately narrower than RFC 3986:

- Absolute roots begin exactly `file:///synthetic/` or `https://example.test/`.
  Relative paths contain one or more ASCII segments; each segment matches
  `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`. Segments `.`/`..` are unsupported.
- No percent escapes, backslashes, authority override, drive/UNC forms, query,
  fragment, userinfo, spaces or non-ASCII URI characters. Out-of-profile URI
  forms are unsupported, not universally unsafe or invalid SARIF. Controls/NUL
  and malformed JSON strings are admission errors. Preserve case exactly.
- Base IDs match `[A-Za-z_][A-Za-z0-9_-]{0,31}`. Base entries may have absolute
  URI or relative URI plus another base ID; directory URI text ends in `/`.
  An omitted URI at a root is retained as a redacted/unknown base. No index
  property in base entries. Cycles are invalid declarations; maximum chain 8.
- Artifact table entries contain a location with URI/base metadata; optional
  self index must equal its array slot. A physical artifactLocation can use URI,
  zero-based artifact index, or both. Index lookup examines only supplied table
  data, never an artifact. Out-of-range index is invalid; bool is not an index.
- URI plus a complete base chain yields concatenated **declared locator text**
  and provenance, never a file/URL access or identity verdict. Missing base ID
  entry, redacted root, or relative URI with no base yields an incomplete symbolic
  locator. Absolute URI plus base ID is invalid for this subset.
- Both URI and index preserve both declarations. Equal complete locator text
  means `declared_locator_match`; a distinct complete text is an invalid conflict
  in this deliberately non-normalizing grammar. If either chain is unknown,
  agreement is unknown/incomplete; never choose the first declaration. No
  cross-run index lookup, artifact-content comparison, dedup or fingerprinting.

Regions support only startLine/startColumn/endLine/endColumn. StartLine is
required when region is present; present values are exact positive integers.
Use specified default startColumn=1 and endLine=startLine, retaining provenance
for defaults. EndColumn is exclusive; a same-line endpoint may equal the start
(an insertion point), but cannot precede it. EndLine cannot precede startLine.
Missing endColumn is an end-of-line marker with unknown numeric bound, not 1
or a guessed character count. Never validate coordinates against real contents.
Absent region is `not_supplied`, with unknown extent. A text region requires
explicit `columnKind` equal to utf16CodeUnits or unicodeCodePoints; preserve it,
never convert units or derive byte/character offsets. Unsupported kinds, binary
regions, charOffset/charLength, snippets/context regions, nested artifacts,
logical/address locations, related locations, external property files, fixes,
fingerprints and producer normalization are explicit unsupported features.

All supplied runs/results/locations remain separate occurrences, including
identical declarations. Empty runs/results are admitted empty metadata, not a
clean scan. Missing/null results mean `results_not_supplied`, incomplete rather
than zero defects. `runs: null` is unsupported in this profile, not collapsed to
empty. Unknown properties are unsupported after common bounded admission.

## Bounds, admission and statuses

Before semantics: maximum 64 KiB UTF-8 bytes, depth 16, 4096 JSON nodes,
1024 characters/string, input/derived locator 512 characters, identifier 64 characters, numeric
lexeme 10 characters, exact integer range 0..2147483647 where applicable. Reject
duplicate keys, BOM, nonfinite numbers, floats, bool-as-int, malformed Unicode
and unsupported Python container types/cycles. At most four runs, 128 artifacts
and 32 base IDs/run, 64 results total, four locations/result, chain depth eight.
Output serialized before emission, maximum 1 MiB. These bound model workload;
they are not OS isolation, wall-time or RSS guarantees.

Priority is whole-document admission first, then full known-profile structural
validation, then unsupported-feature scan, then reference/region interpretation.
No projected locations are released after any malformed/invalid/conflicting
known declaration, even late or unreferenced. Check base graph cycles globally.
Bounded unknown schema/version/profile values are unsupported only after validating
the common envelope/container limits; this does not validate future semantics.
No partial location projection after any unsupported feature either. Incomplete
is reserved for admitted known-profile missing declaration context/extent.

Report status/exit: `interpreted`/0, `incomplete`/2, `unsupported`/2, `invalid`/2;
CLI misuse or output failure nonzero with fixed, inert diagnostics. No status
asserts vulnerability presence/absence, correctness of actual locations or SARIF
conformance. Invalid/unsupported output has reason codes and input indices, no
computed rows or raw message excerpts. Supported rows retain original indices,
explicit/defaulted/unknown fields and declaration provenance. Row provenance stores indices/base IDs and bounded input pointers, not repeated whole input/base/artifact objects. Errors before
serialization never leak partial semantic rows. stdout delivery can fail/partially
write: handle short writes, broken pipe and flush failure honestly, without a
success claim; no transactional stdout guarantee.

## Architecture and threat model

Thin CLI -> bounded duplicate-aware decoder -> profile admission -> supplied
reference/base interpreter -> region projection -> bounded inert serializer.
Pure model functions take admitted dictionaries and return data, without I/O.
No general urllib/path resolver is needed for the restricted segment grammar.
Keep schema references as text, not imports. No candidate source is executed or
copied; source links/notices and AI assistance remain documented.

| Threat | Control/limit |
| --- | --- |
| Locator drives filesystem/network access | No resolving I/O APIs in model; stdin/stdout only; synthetic URI roots; patched denied-I/O seam tests |
| Index ambiguity/cross-run confusion | Typed bounds, retained indices, same-run lookup, dual-declaration agreement; no dedup |
| Cycle/size exhaustion | Whole-input bytes/tokens/depth/count guards, iterative bounded traversal, output cap |
| Invented region certainty | Explicit unit/default provenance; unknown end-of-line length, no source lookup/unit conversion |
| Report injection | ASCII JSON escaping, fixed diagnostics, no clickable rendered URLs/HTML/ANSI or target-controlled filenames |
| Misleading equivalence | Exact declaration labels only; no authenticity/content/diagnostic/root-cause claim |

## Independent oracles to freeze before implementation

Unless a case expressly tests absence, text-region cases supply a supported columnKind. Author expected JSON projections from these hand cases without calling model
helpers. Cite normative source sections separately from lab-profile restrictions.
Use no worker output or candidate library as an oracle.

| Case | Expected distinction |
| --- | --- |
| Absolute synthetic locator | Retained text/provenance, no artifact existence claim |
| ROOT=file:///synthetic/project/, SRC=src/ + ROOT, leaf=a.c + SRC | Declared text file:///synthetic/project/src/a.c; chain retained |
| Same leaf and different base roots | Different declarations retained; no dedup |
| Index 0 and an exact matching direct locator | declared_locator_match, both provenance paths |
| Index equal to artifact count, or bool index | invalid; zero projected rows |
| Complete dual declarations disagree | invalid conflict, no first/last selection |
| Missing base entry or root without URI | incomplete symbolic chain, not empty/guessed root |
| A->B->A including unused cycle | invalid globally; no projections |
| startLine=3, endColumn=5 with other coordinates absent | startColumn=1/default, endLine=3/default, exclusive endpoint 5 |
| startLine=3 with endColumn absent | Unknown numeric end-of-line bound; incomplete extent |
| (3,4)->(3,4), compared with (3,4)->(3,3) | Insertion point admitted versus reversed region invalid |
| Same coordinates under both column kinds | Retain distinct unit labels; no offset conversion/equality claim |
| Byte region or parent/percent URI segment | unsupported, no normalization or file access |
| No locations / null results / empty results | Missing extent / unavailable result context / empty supplied metadata distinguished |
| Valid first result, malformed late result | Whole report invalid with zero projected rows |

## Stages and definitions of done

1. **Freeze contract/oracles after approval.** Specify exact field allowlists,
   validation precedence, all reason codes and output schema. Independently author
   and freeze the above expected cases plus paired repairs. Do not change expected
   labels merely to match implementation. Dependencies: approval; source sections
   and URI/profile restrictions are already recorded. Done: reviewed fixture hashes.
2. **Implement one bounded interpretation slice, then references/regions.** Deliver
   strict decoder + absolute synthetic location + CLI; then base/index/region
   handling and complete unsupported paths. Verify pure seams deny artifact I/O,
   source/URL/schema lookup and subprocess. Normal/optimized unit and real CLI
   tests, max admitted document/report fit, short/flush/broken-output tests. Done:
   every fixed oracle passes, no partial semantic report on late failure.
3. **Review and portfolio handoff.** Four meaningful killed mutations: missing
   index range check, ignored base cycle, guessed missing endColumn, erased column
   kind; assertion-detected behavior differences, source restored and rechecked.
   ECC actual-change self-review, installed Bandit with transparent dispositions,
   source/fixture/receipt hashes, README/demo, MIT/attribution/AI disclosure,
   STATE/DECISIONS/LEARNING and vault milestone. No arbitrary coverage target.
   Done: focused receipts and limitations match observed commands; no publication.

Stages 1–3 are locally complete; see VERIFICATION.md and REVIEW.md for actual
outcomes. Repository creation, installs, scanner/VM
changes, real reports, hosted CI and publication are not authorized. Ready for
local review, not production use.

## Approved addendum and authority

The coordinator's 03:06 SUCCESSORS.md approval covers stages 1–3. Original
human authority was independently retrieved from coordinator chat user turns
01a10a45-2549-7333-8a33-edd64a1dd4fa and
01a10a4f-2230-7433-90e7-e2cff1fa15e9: Jake delegated plan approval/start
and related successor labs. The recovery message grants no additional authority.
CONTRACT.md freezes the exact profile, aggregation and reason precedence before
application code. Missing text columnKind is invalid; bounded unknown kinds
unsupported; wrong types invalid. Directory bases require a terminal slash.
Unused declarations and graphs receive known validation before unsupported
status. Missing results/locations/region/endColumn remain explicit incomplete
context, while supplied empty arrays are metadata only. Mutations must cause
the intended assertion failure, not an application crash.
