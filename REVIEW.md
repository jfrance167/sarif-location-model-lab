# ECC actual-change self-review

October 5, 2026; implementing agent performed the review, not an independent
reviewer. Applied C:/Users/Jake/.codex/skills/ecc-code-review/SKILL.md and its
pinned reviewer checklist, then ECC verification-loop for evidence consolidation.
Scope: complete original model.py, cli.py, verify.py, tests/test_model.py,
research author/example utilities, their callers, frozen expectations and outputs.
All are untracked task additions; no baseline application existed. Parent
checkout and unrelated work preserved.

## Concrete findings and repairs

| Trigger / bad outcome | Final location / repair | Evidence |
| --- | --- | --- |
| Table URI omitted but base ID supplied lost symbolic chain | model.py reference(), line 337 onward; retain chain without guessing text | redacted_table_uri_retains_chain |
| Unused composed base locator could exceed bound without validation | model.py validate(), line 250 onward; derive every supplied base/table declaration | unused_base_locator_bound |
| Earlier run conflict could precede later run global cycle | model.py validate(); all graphs pass before references | global_graph_precedes_earlier_conflict |
| Index with redacted direct base modifier dropped supplied provenance | model.py artifact_projection(), line 386 onward; preserve symbolic direct declaration and unknown agreement | index_with_redacted_direct_modifier |
| C1 URI controls returned unsupported instead of frozen invalid label | model.py artifact(); cover C0/C1/DEL | uri_subset_and_malformed |
| Closed stdout buffer flushed again during interpreter exit; exit 120 and extra diagnostic | cli.py process exit, line 56 onward; detach already-failed stdio, no new device/file | raw initial/closeout pipe logs; actual_closed_pipe_and_help |

Findings were bounded correctness issues (MEDIUM); no independent audit or
hostile-execution security certification is implied. Additional verifier repairs:
bounded communicate rather than blocking stderr read, and exact LF/CRLF
diagnostic comparison. Re-read repaired application paths; affected full normal/
optimized checks passed. No remaining actionable defect identified within review
scope. File/line locations refer to the final saved source, not a PR diff.

## Focused diagnostic repair after coordinator review

Coordinator's barrier-controlled reproduction of --bad-synthetic-argument with
closed stderr returned 120 in normal/-O. Confirmed MEDIUM correctness defect:
cli.py diagnostic() swallowed failures and misuse returned2, bypassing stdio
detachment. Re-read diagnostic(), main() and standalone exit/callers/tests.
Final cli.py:16 defines diagnostic() using deliver() to check write count/flush,
returning a
boolean; misuse branch cli.py:39 returns3 on failed diagnostic, 2 only on complete
delivery. The existing operation-failure shutdown path handles both sinks.
Review found no additional actionable defect in these repaired paths. Error
reporting remains best-effort when stderr fails, as frozen in DELIVERY.md.

35 tests pass normal/-O, including three added test methods: diagnostic short/
None/bool counts, flush/write failures, and ten barrier-controlled child scenarios
per suite (five cases x normal/-O). Misuse closed-stderr/both-sinks and help/report
both-sinks return3; a report with unused stderr closed still succeeds. Original
successful report/help and all frozen full oracles remain covered. Current code
receipt is .private/verification-stderr-repair/receipt.json. This is implementing-
agent self-review of the correction; the coordinator reproduction is separate
focused evidence, not an independent audit of the whole application.

## Installed Bandit dispositions

Application: model.py/cli.py, exit 0, zero findings, zero errors, no suppressions.
Harness: verify.py/tests/test_model.py/research/author_oracles.py, exit 1,
nine unsuppressed LOW advisories: B404 for two subprocess imports, B603 for
seven subprocess call sites. Separate research/save_examples.py: exit 1, two
unsuppressed LOW B404/B603 advisories. Raw JSON retains exact current lines.
All commands use sys.executable, owned literal script/module paths and structured
arguments, shell=False default; synthetic JSON is stdin data. No input selects an
executable or shell expression. The mutation harness executes only four explicitly
reviewed modifications of owned model code. No skips/nosec/broad suppressions.
These advisory dispositions are self-review judgments, not a clean whole-project
SAST verdict. Installed Bandit is verification-only, never a product dependency.

## Limits

Finite synthetic checks, Windows CPython 3.13.7 only. No real reports/artifact
access, full SARIF/URI conformance, file identity, defect truth, hard time/RSS
isolation, Linux/hosted or independent review proof. The application is inert;
tests are not an adversarial sandbox certificate. No new Git repository, remote
workflow, push, merge, publication, shared-helper or scanner/VM changes.
