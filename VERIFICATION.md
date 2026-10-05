# Verification record

October 5, 2026; Windows x64 CPython 3.13.7. Final code evidence at
`.private/verification-stderr-repair/receipt.json`; raw stdout/stderr and separate
mutant directories are retained there. Earlier failed receipts preserved under
verification-initial and verification-final, repaired intermediate evidence under
verification-reviewed. Prior verification-closeout passed its narrower suite
but missed failed misuse stderr; coordinator reproduction is retained at
.private/coordination/2026-10-05/evidence/0405-sarif-cli-review.json in the parent
workspace. It observed exit120 in normal and -O. The repair receipt supersedes
that narrower code receipt; original evidence is preserved.

| Check / actual command | Outcome |
| --- | --- |
| python -m unittest discover -s tests -v | 35 passed, exit 0, no skips |
| python -O -m unittest discover -s tests -v | 35 passed, exit 0, no skips |
| python verify.py .private/verification-stderr-repair | exit 0, passed=true; complete raw logs/hashes |
| python -m bandit model.py cli.py -f json | exit 0, zero findings/errors |
| python -m bandit verify.py tests/test_model.py research/author_oracles.py -f json | exit 1, nine LOW findings, zero errors; retained |
| python research/save_examples.py | exit 0; eight real CLI outputs match independent complete expectations |
| python -m bandit research/save_examples.py -f json -o .private/verification-closeout/bandit_examples.json | exit 1, two LOW findings, zero errors; retained |

The verifier uses the installed absolute Python executable; receipt records
actual argument arrays. Full tests execute 27 frozen cases through real CLI in
each suite, compare entire reports and exact status exits. Normal/optimized
application smoke checks and report/help closed-pipe checks also run. The process
boundary fix changed failed pipe exit 120 to 3 with only the fixed diagnostic.
Windows text stderr uses CRLF; JSON stdout is binary ASCII with LF. The repair
adds short/None/bool diagnostic-write and diagnostic flush/write failure checks.
Five barrier-controlled child scenarios run normal and -O in each suite:
misuse with stderr closed; misuse/help/report with both sinks closed (all exit3);
successful report with unused stderr closed (exit0 and exact report). All use
unittest assertions unaffected by optimization. DELIVERY.md fixes the policy.

Four copied-code mutations were each killed by `AssertionError` containing
FROZEN_ORACLE_MISMATCH and `FAILED (failures=1)`, exit 1, zero error/crash verdicts:
index range guard removed; base cycle guard removed; absent endColumn guessed 1;
column kind forced UTF-16. Original source was never replaced and its unchanged
hash is recorded. Every mutation uses an independently frozen complete report.

Other material checks: exact 64 KiB raw input succeeds and +1 byte rejects;
duplicates/BOM/floats/nonfinite/long numeric tokens/invalid UTF-8/surrogates/
depth/nodes/custom objects/cycles reject; region/index bools reject; late malformed
and unused declarations release no rows; eight-base versus nine-base chains;
dual conflict versus unknown agreement; missing context/empty metadata;
256 occurrences fit admitted input and serialized output, with reduced-output-
limit refusal. Limits are conjunctive; not every combination of individual
maxima is admitted. No hard process memory/time guarantee is asserted.

Model and injected CLI paths run with open/socket/Popen/os.system/os.getenv
denied. Application AST imports exactly json/re and sys/model, with selected
dynamic execution/file calls absent. This is focused seam/source evidence, not
proof against every possible Python capability or a malware isolation boundary.

Example helper/output bytes were unchanged by this repair; prior exit0 and
two LOW SAST results remain evidence, not a claimed helper rerun. Current
actual-CLI oracle tests still compare the same complete report values.
SAST dispositions and exact reviewed fixes are in REVIEW.md. No additional
checker was installed. Product has no third-party dependency manifest/lockfile
requirement. No owned GitHub repository was created or targeted: hosted
CodeQL/protections/secret scanning are not applicable to this local scope, never
claimed passed. Task source/docs/fixtures were inspected for private material;
only invented fixtures and public source/worker metadata were found. No dedicated
secret-scanner/history audit or independent source review was performed.

Final delivery manifest separately hashes documentation, examples and code.
Frozen oracle receipts are checked by the test suite. Sources and candidate
revision evidence remain under research/. No real/private reports, referenced
files, networks, scanner/VM controls or publication were tested or changed.
Linux/other Python versions, full SARIF validation, artifact identity and
diagnostic/vulnerability correctness remain unverified/outside profile.
