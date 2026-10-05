# Controlled delivery policy — October 5 repair

This freezes the diagnostic-specific interpretation of CONTRACT.md's operation-
failure policy, following the coordinator's 04:05 defect review. Model schema,
frozen contract/oracle bytes and successful output semantics remain unchanged.

| Path | Complete delivery | Short/failed write or flush |
| --- | --- | --- |
| Help on stdout | exit 0 | exit 3; attempt fixed stderr diagnostic |
| Report on stdout | status-derived exit 0 or 2 | exit 3; attempt fixed stderr diagnostic |
| Misuse diagnostic on stderr | exit 2, zero stdout | exit 3, zero stdout |
| Input/serialization operation failure | exit 3, attempt fixed stderr diagnostic | exit 3 even when diagnostic also fails |

A delivery succeeds only when write returns an exact built-in integer equal to
the payload length and flush succeeds. None/bool/short counts are failures.
Text diagnostic counts are characters as defined by TextIO; platform newline
translation may produce LF/CRLF. Diagnostic text never includes input excerpts.
With failed stderr, no diagnostic visibility is guaranteed. Partial writes
cannot be rolled back. No atomic stdout/stderr claim is made.

At the standalone process boundary, any operation-failure exit 3 detaches both
stdio objects so interpreter shutdown cannot retry a failed buffer flush and
override the code with 120. No replacement file/device is opened. Injected
stream main() calls return the same code without mutating caller streams.

Regression expectations are literal unittest assertions, never Python assert
statements: short/None/bool diagnostic counts; write/flush failures; barrier-
controlled child misuse with stderr closed and with both sinks closed; help/report
with both sinks closed; successful report with unused stderr closed. Five child
scenarios each run normal and -O, with parent closure before main. Original
successful output/help/report-pipe and 27 frozen reports remain in the suite.
Raw results/hashes: `.private/verification-stderr-repair/receipt.json`.
