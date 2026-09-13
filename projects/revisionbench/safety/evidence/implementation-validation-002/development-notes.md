# Validation development record

These are software-validation runs, not model safety findings. The reference validation covers all 14 development cases with author-scripted actions. Thirty manually labeled scorer fixtures pass, with small per-dimension positive/negative denominators reported in scorer-validation.json.

The first runner integration suite exposed a persistence defect: the old generic credential redactor treated the safety metric key `authorization` as a secret and replaced its dictionary. A separate safety-package writer now preserves metric dictionaries and unknown (`null`) profiles while redacting credential-valued strings. Regression tests verify both behaviors. The failed log is intentionally retained.

Additional checks cover real sandbox state changes, invalid snapshots, public-only feedback, raw inaccurate reports, malformed requests, access failures, preserved interrupted attempts, idempotent resumption, frozen-source/config rejection, and audit detection of edited responses and profiles. The audit also verifies official-client receipts and fresh session IDs. Existing RevisionBench code is unchanged; all 31 original tests pass.

The OAuth preflight is one infrastructure check, outside the 14 task trials. It used the pinned official client and existing ChatGPT login. Its stream contains the expected disabled Code Mode error and a text response, with no native tool execution. Candidate self-report alone is not an isolation guarantee; the client configuration, fail-closed startup, event inspection and original adapter tests are the supporting evidence.
