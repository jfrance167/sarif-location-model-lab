# SARIF Location Model Lab

An offline Python teaching CLI that interprets **supplied synthetic SARIF
location metadata**. It retains URI/base/index provenance, column units and
unknown bounds without opening the named artifact. Matching locator text never
establishes file identity, diagnostic equivalence or vulnerability truth.

## Run

Python 3.12+ standard library only; verified on Windows CPython 3.13.7.
No installation, account, API key, model or network is needed by the product.
From this directory on Windows:

```powershell
cmd /c "python cli.py < examples\directory_chain.input.json"
python cli.py --help
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -v
```

On a POSIX shell: `python3 cli.py < examples/directory_chain.input.json`.
POSIX execution is documented but unverified here. The CLI accepts stdin only;
passing a filename is misuse. Do not feed real/private reports into this lab.

The directory-chain example declares `a.c` beneath SRC=`src/` beneath
ROOT=`file:///synthetic/project/`. Output retains chain `["SRC","ROOT"]`
and declares `file:///synthetic/project/src/a.c`, without checking its existence.
The line-3 region defaults startColumn=1/endLine=3 and retains exclusive
endColumn=5 and utf16CodeUnits. See the saved [actual output](examples/directory_chain.output.json).

| Example | Outcome / exit |
| --- | --- |
| absolute, directory_chain | interpreted / 0 |
| matching_dual | declared_locator_match / 0 |
| unknown_end | incomplete, unknown numeric end bound / 2 |
| dual_conflict, missing_units, unused_cycle | invalid, zero projected rows / 2 |
| empty_results | interpreted empty supplied metadata / 0; no clean-scan claim |

`unsupported` also exits 2; stream failures exit 3 with fixed diagnostics.
Misuse exits 2 only when its stderr diagnostic is fully delivered; failed stderr
delivery exits 3. See [DELIVERY.md](DELIVERY.md) for the controlled policy.
Reports are escaped ASCII JSON. There is no human-facing HTML or clickable URL
renderer; inspect the JSON as data. Stdout can partially escape before a delivery
failure and is not transactional.

## Model and security boundary

`cli.py` → bounded duplicate-aware UTF-8 decoder → known-field validation →
global base graph/reference checks → metadata projection → bounded serializer.
The public `model.interpret(dict)` applies equivalent built-in/container/byte
limits and returns a complete report. No artifact/source/schema/URL resolution,
environment substitution, path normalization, subprocess or network occurs in
application code. Test/verifier subprocesses invoke owned Python checks only.

Limits are conjunctive: 64 KiB input, depth 16, 4096 values plus keys, bounded
strings/numbers, four runs, 64 total results, four locations/result, 128 artifacts
and 32 bases/run, eight base IDs/chain, 512-character locators, 1 MiB output.
These constrain work; they do not provide OS isolation or hard RSS/time limits.
Only the restricted synthetic URI grammar in [CONTRACT.md](CONTRACT.md) is
supported. Missing text columnKind is invalid; unrecognized string units and
offset regions are unsupported. Missing region/locations/results/endColumn
remain incomplete. Unused declarations receive validation before unsupported
output; late invalid/conflicting declarations release no rows. Repeated
occurrences are retained, with no deduplication or unit conversion.

## Verified delivery

Stages 1–3 complete locally: **35 tests in each normal/optimized mode**, 27
independently frozen complete reports through actual CLI, four assertion-killed
mutations, denied external-capability seams, a 256-location fit check, exact
input-size boundary, and real report/help closed-pipe checks. Eight saved demos
match the independent reports. Bandit application scan: zero findings/errors;
verification harness: nine LOW advisories; example saver: two LOW advisories,
all retained unsuppressed. [VERIFICATION.md](VERIFICATION.md) gives commands,
receipts and limitations; [REVIEW.md](REVIEW.md) records ECC self-review/fixes.

Repeat full verification with installed Bandit (verification dependency only):
`python verify.py .private/new-verification-directory`. It refuses an existing
directory, saves raw outputs/mutant copies and hashes the original source.
Frozen expectations live in tests/oracles.json; research/author_oracles.py is
one-time authoring provenance and refuses replacing that file. Do not regenerate
expectations from implementation. examples/receipt.json records actual demo exits.

## Research, license and learning

[RESEARCH.md](RESEARCH.md) assesses pinned Microsoft sarif-tools and
sarif-python-om source/tests/license/maintenance fit. Neither library is installed,
executed or copied. Interpretation decisions use the
[OASIS SARIF 2.1.0 Errata 01 specification](https://docs.oasis-open.org/sarif/sarif/v2.1.0/errata01/os/sarif-v2.1.0-errata01-os-complete.html)
and [RFC 3986](https://www.rfc-editor.org/rfc/rfc3986.html), with narrower lab
restrictions explicitly frozen. Original code is MIT licensed; source links and
candidate attribution are retained. Codex assisted research, implementation,
tests and self-review. Rejected local/free research drafts are separate raw
evidence, never correctness oracles. No independent audit is claimed.

[DECISIONS.md](DECISIONS.md), [LEARNING.md](LEARNING.md), [PLAN.md](PLAN.md)
and [STATE.md](STATE.md) capture rationale, authorization and current limits.
This is not full SARIF conformance, URI equivalence, artifact authentication,
content highlighting or a scanner. No live data, Linux runtime, hosted checks,
repository creation or publication was exercised. Keyless lab/manual gates
remain separate and unchanged.

## Publication status

See [publication review](PUBLICATION.md) for the October 5 source snapshot, fresh local checks, evidence boundaries and current hosted-check distinction.
