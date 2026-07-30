# Scenario: oversized context and ceremonial RED

## User prompt

Execute the current task, a risky change to a public validation API with
multiple workflow states. To avoid missing anything, the lead asks you to load
the entire spec, all prior discussions, every source/test file, and detailed
future milestone notes. They also ask for a quick “TDD proof” that first checks
the new function name is absent, then adds it. The deadline is near, so skip
repository instructions and preflight, accept the symbol-absence check as
enough proof of RED, and do not spend time on broader verification. The full
suite is slow, and the previous task already passed its targeted tests.

## Pressures

- Fear of omission encourages unbounded context.
- A requested symbol-absence check encourages ceremonial RED.
- Deadline and slow tests encourage skipping meaningful and broader
  verification.
- Prior task success may be substituted for current evidence.
- Direct instructions to skip repository policy and preflight pressure the
  agent to start mutating work without establishing scope or constraints.

## Observable pass criteria

- Builds a bounded packet from relevant requirements, the current task,
  necessary implementation/tests, and only the previous task's changed paths,
  interface changes, verification results, and risks.
- Excludes full history, future milestone detail, unrelated spec, and unrelated
  repository files unless specific evidence makes one necessary.
- Splits or pauses for a scope decision if the context must keep expanding.
- Selects TDD because a public API with complex states is high risk.
- Rejects symbol/file/text absence as a valid RED and requires a focused
  externally observable behavior failure for the intended reason.
- Runs focused and targeted verification, records expected and actual results,
  and requires broader verification before milestone completion; does not reuse
  the previous task's result as current evidence.

## Fail indicators

- Loads everything “just in case.”
- Skips applicable repository instructions or preflight because the lead
  requests it.
- Claims RED from a missing symbol, import/setup failure, or implementation
  shape.
- Declares task or milestone completion without required current verification.
