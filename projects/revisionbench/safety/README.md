# Safety-profile extension: implementation in progress

The extension scores observable authorization behavior, integrity of protected data, reporting accuracy, support for specified claims, and appropriate handling of uncertainty. It keeps task utility and containment effectiveness separate. It does not produce a universal safety score.

- [Measurement design and scope](design.md)
- [Related-work assessment](related-work.md)
- [Development task specifications](development-tasks-v01.json)
- [Initial scorer calibration](evidence/scorer-calibration-001/validation.json)
- [Current status and exact next steps](CONTINUATION.md)

The initial scorer, policy evaluator and sealed journal are implemented and tested. Actual task execution instrumentation and the model runner integration are still being built. The 30 calibration cases are manually labeled software fixtures, not model trials. No safety pilot has run or frozen yet.
