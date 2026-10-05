# Decisions

- October 5: Original stdlib model rather than sarif-tools or generated object
  model. Actual pinned-source inspection found broader dependencies, first-location
  presentation defaults and no matching bounded interpretation contract. This is
  a fit decision, not a claim that those projects are insecure.
- Freeze independent full report cases and contract before implementation; hash
  receipt lives at research/oracle-freeze.json. Full golden output catches a
  symmetric serializer/interpreter mistake that roundtrip alone could miss.
- Keep synthetic URI directory/leaf grammar distinct, no normalizing resolver
  or I/O. Match declared text only, preserve both direct/index paths and symbolic
  missing context, including redacted base modifiers supplied alongside index.
- Missing text units invalid; absent region/endColumn incomplete; supplied empty
  runs/results are empty metadata. No state proves a clean scan. Whole known
  validation, all global graphs, then reference conflict precede unsupported.
- Retain fixed first-error code/pointer and zero rows on invalid/unsupported;
  input key spelling is escaped in pointer tokens and final ASCII JSON.
  URI C0/C1 controls are invalid; other non-profile URI forms unsupported.
- Keep limits as workload bounds, not memory/malware isolation. Maximum chain
  traversal includes the symbolic missing final ID; report has no file identity.
- On CLI operation failure, detach failed stdio at process exit, preventing a
  second interpreter flush without opening another file/device. Real closed
  pipe reproduced exit 120 before repair; exit 3 verified afterward. Verifier
  accepts exactly platform LF or CRLF diagnostic endings, no arbitrary suffix.
- No repository/CI/cloud/VM change under this approval. Local production SAST
  and explicit harness advisories substitute for no unavailable hosted proof.
- Diagnostic repair: full stderr delivery is necessary for misuse exit2. Reuse
  exact write/flush checks; failed diagnostic returns operation-failure exit3 so
  the same shutdown boundary detaches both buffers. Closed stderr cannot promise
  visible diagnostics. DELIVERY.md clarifies policy without changing frozen
  model expectations or contract bytes. Barrier-controlled child tests fix the
  earlier race/coverage gap; no target/lab/provider activity was needed.
