# SARIF location-model research

Reviewed October 5, 2026. Research/plan only under the coordinator's 02:41
SUCCESSORS.md decision. No project implementation or upstream code execution.

## Reuse and alternatives

Focused local README/STATE searches for SARIF, diagnostic deduplication and base
URIs found no matching project. Relevant existing material is the Keyless
scanner's conservative diagnostic grouping, exact build identity, inert reports
and explicit unknown locations; these concepts are reusable, not its Linux
execution boundary. Direct vault keyword searches found no SARIF-specific note.
Home/Codex Integration and the existing scanner milestone were consulted. This
is a focused overlap check, not an exhaustive inventory. GLPI was not imported.

Two candidates: (1) synthetic SARIF reference/base/region interpretation;
(2) generic diagnostic grouping by tool/build/category/location. Prefer (1):
(2) overlaps the scanner and tempts a same-root-cause claim from weak keys.
Location declarations instead teach how metadata can be precise yet insufficient
for artifact identity, highlighting, authenticity or defect equivalence.

## Primary semantics reviewed

[OASIS SARIF 2.1.0 plus Errata 01](https://docs.oasis-open.org/sarif/sarif/v2.1.0/errata01/os/sarif-v2.1.0-errata01-os-complete.html),
sections 3.4, 3.14.14, 3.14.27 and 3.29-3.30: artifact locations use URI/index
metadata; both declarations must agree. Base IDs refer to supplied URI metadata.
Line/column coordinates are one-based; endColumn is exclusive. Missing startColumn
and endLine have specified defaults; a numeric missing endColumn depends on
unavailable line contents. ColumnKind distinguishes UTF-16 units from Unicode
code points. Content-free inspection cannot convert units or validate a region
against an actual artifact. The model is not a complete SARIF validator.

[Approved errata](https://docs.oasis-open.org/sarif/sarif/v2.1.0/errata01/os/sarif-v2.1.0-errata01-os.html),
issues 458, 460/461 and 480: trailing slashes in base examples matter; file-URI
parent segments cannot simply be normalized away because filesystem semantics
can differ. [RFC 3986](https://www.rfc-editor.org/rfc/rfc3986.html) is a URI syntax
reference, not evidence that a locator names a real file. Proposed profile
intentionally excludes dot/parent segments and general URI normalization.

## Open-source assessment

Connected GitHub repository search succeeded. Some fetches failed transport;
public web access supplemented them, and later connected pinned-file reads
succeeded. No repository was cloned, installed or executed. No current upstream
CI success, advisory completeness, Scorecard result or confirmed safety claimed.

### microsoft/sarif-tools

Reviewed commit `5b8d9e65c1b2cc04ab3af25f012ce23ab8106033`, commit date
2025-08-29; pyproject version 3.0.5. Actual
[location reader](https://github.com/microsoft/sarif-tools/blob/5b8d9e65c1b2cc04ab3af25f012ce23ab8106033/sarif/sarif_file_utils.py)
selects a first-location path/line and does not model base-ID chains/index-only
references. [record conversion](https://github.com/microsoft/sarif-tools/blob/5b8d9e65c1b2cc04ab3af25f012ce23ab8106033/sarif/sarif_file.py)
uses line 1 when no line is found. That presentation behavior is unsuitable for
this lab's explicit unknowns; this is a fit assessment, not an exploit claim.
[Loader](https://github.com/microsoft/sarif-tools/blob/5b8d9e65c1b2cc04ab3af25f012ce23ab8106033/sarif/loader.py)
walks/globs files and uses ordinary json.load, outside the proposed stdin-only
bounded contract. Utility and CSV tests were read, including a concrete physical
URI/startLine example; no upstream test was run.

[pyproject](https://github.com/microsoft/sarif-tools/blob/5b8d9e65c1b2cc04ab3af25f012ce23ab8106033/pyproject.toml)
adds Jinja2, jsonpath-ng, matplotlib, python-docx and PyYAML, unnecessary here.
[Validation workflow](https://github.com/microsoft/sarif-tools/blob/5b8d9e65c1b2cc04ab3af25f012ce23ab8106033/.github/workflows/validation.yml)
configures Poetry/Ruff/pytest on Python 3.8; build workflow packages a wheel.
Actions use version tags at this inspected commit, not immutable pins.
Open [issue 110](https://github.com/microsoft/sarif-tools/issues/110) reports
location-prefix display loss; [issue 104](https://github.com/microsoft/sarif-tools/issues/104)
discusses unstable line-based fingerprints. These are reported behavior, not
reproduced findings. Source/tests support using it for comparison, not importing
its broad processing pipeline. MIT license inspected; copying substantial code
would require its notice. No candidate code copied into the proposed model.

### microsoft/sarif-python-om

Reviewed commit `f99b8edb126e2a4ad8a61ffee63113887a6af035`, commit date
2021-02-03. Repository metadata says non-archived; push timestamp 2024-04-03 does
not establish newer default-branch code. Actual generated
[ArtifactLocation](https://github.com/microsoft/sarif-python-om/blob/f99b8edb126e2a4ad8a61ffee63113887a6af035/sarif_om/_artifact_location.py)
and [Region](https://github.com/microsoft/sarif-python-om/blob/f99b8edb126e2a4ad8a61ffee63113887a6af035/sarif_om/_region.py)
are attrs classes with defaults, not the bounded semantic/reference interpreter
needed here. README describes schema generation. setup.cfg requires attrs and
pbr; setup.py uses pbr setup requirements. MIT license inspected. No tests/CI
paths appeared in the inspected repository tree; no passing-suite claim. Avoid
this extra object-model dependency for a tiny dictionary-based subset.

The larger microsoft/sarif-sdk was screened from repository metadata only;
source/CI/license assessment was not completed and it is not recommended for
adoption in this plan. Metadata's NOASSERTION license is not a legal conclusion.

## Recommendation and worker evidence

Build a small original stdlib teaching model, not a fork/full SARIF engine.
Reference pinned candidate behavior and OASIS sections; do not copy a schema or
specification wholesale. Retain attribution and any applicable notices if reuse
changes. No additional runtime packages, installations, models or accounts.

Local qwen3.5:2b drafting: sandbox loopback EACCES, followed by one approved local
access attempt; output truncated at 500 tokens and confused invalid/unsupported
labels and unavailable file bounds. Rejected. Raw output/metadata preserved in
research/. Read-only worker refresh verified configured free-only restrictions
and live OpenRouter zero pricing. One explicit public synthetic OpenRouter draft
returned no text; no retry/provider switch/paid fallback. Failure is saved in
research/worker-failure.json. Codex completed source verification/design; no model
output supplies a semantic oracle. Laya's tested classifier/triage schemas do not
help this precise standards task; it was not invoked.

## Remaining uncertainty

No code or fixtures/tests exist yet. No full standards conformance, URI equivalence,
source-file identity/encoding/line-length, upstream execution, hosted CI, real
reports, vulnerability truth or security certification. The explicit proposed
subset and independent oracles in PLAN.md must be approved before implementation.
