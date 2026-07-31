# M05 Evaluation Runbook

M05 evidence is recorded only after an evaluator has reviewed the complete
prompt, actual decision, and verbatim rationale. Do not place secrets, real
home paths, repository-external paths, or unrelated-project content in a
prompt or evidence file.

## Offline workflow

Generate a schema-v2 case-bound template without calling a client. CP-09
reruns bind the archived run and approved change proposal into the template:

```text
python tools/evaluate.py prepare --case gate-baseline --client codex --run-id baseline-gate-02 --rerun-of baseline-gate-01 --change-proposal CP-09
```

Fill the template outside the repository after an approved fresh client
session. Keep the generated `attempt_id` and `prepared_at`; record a unique
non-sensitive `session_ref`, exact Codex CLI version, explicit model, config
snapshot, `runtime_surface`, and a later UTC `recorded_at`. Record it once:

```text
python tools/evaluate.py record --input <completed-record.json> --evidence-dir evaluation/evidence
```

The CLI writes evidence only below this repository. The baseline, pressure, and
wording cases are the Codex reference matrix and must use `client_id: "codex"`.
Their schema-v1 records are preserved unchanged under
`evaluation/archive/cp09/` and are excluded from active counts. Active CP-09
records use baseline/loaded suffix `02` and wording suffixes `06`–`10`.

CP-10 is one exact active-to-active rebuild of the commit-boundary wording
group. Keep CP-09 runs `06`–`10` unchanged. After separate external-client
approval, prepare only these five pairs; each template binds its source as both
`rerun_of` and the sole `supersedes_run_ids` entry:

```text
python tools/evaluate.py prepare --case wording-commit-boundary --client codex --run-id wording-commit-boundary-11 --rerun-of wording-commit-boundary-06 --change-proposal CP-10
python tools/evaluate.py prepare --case wording-commit-boundary --client codex --run-id wording-commit-boundary-12 --rerun-of wording-commit-boundary-07 --change-proposal CP-10
python tools/evaluate.py prepare --case wording-commit-boundary --client codex --run-id wording-commit-boundary-13 --rerun-of wording-commit-boundary-08 --change-proposal CP-10
python tools/evaluate.py prepare --case wording-commit-boundary --client codex --run-id wording-commit-boundary-14 --rerun-of wording-commit-boundary-09 --change-proposal CP-10
python tools/evaluate.py prepare --case wording-commit-boundary --client codex --run-id wording-commit-boundary-15 --rerun-of wording-commit-boundary-10 --change-proposal CP-10
```

Partial, extra, cross-case, unapproved, non-passing, environment-changed, or
identity-reused CP-10 rebuilds fail closed. The effective summary excludes
superseded records only after the complete later `5/5 PASS` group validates;
all 16 CP-09 active source records must retain their approved semantic hashes
and remain in place for audit. Every replacement must be prepared after its
mapped source was recorded and after the run 07 trigger.

Every completed record includes a `reason` for a `fail` or `blocked` outcome,
minimal approved `notes`, and a rationale review with an optional
`change_proposal_id`. Successful or observed runs leave `reason` empty.
The baseline and paired pressure record must use identical client version,
model, config, and runtime surface. Each wording group must also keep one
environment while using five distinct attempt IDs, session references, and
recording timestamps.

Validate and summarize only recorded evidence:

```text
python tools/evaluate.py validate
python tools/evaluate.py summary --format json
```

## External-client boundary

Before installing, logging in, accessing a network, or launching any client,
obtain a separate approval. Use an isolated project root and the M04 installer:

```text
python tools/install.py --client <id> --scope project --project-root <isolated-root>
```

For every client, record its version, exact command or UI action, observable
Skill discovery/smoke result, and verbatim output. A missing client, login,
network condition, timeout, or interrupted run is `blocked`, never `pass`.

On 2026-07-31 the user retained ownership of the eight-client live
discovery/smoke matrix and directed the repository release closeout to proceed
without those runs. No `client-*.json` files are included in the M05 candidate,
and the unfiltered `validate` command therefore remains an intentional
fail-closed check until the user records the external results. The repository
release evidence covers only the filtered baseline, pressure, and wording
matrix; it does not imply `5/5` Level 1 or `3/3` Level 2 completion.

## Rationale review

Use `no-new-rationale` when the reason is already covered by existing rules.
If a new reason attempts to bypass a rule, record `new-rationale`, stop the
matrix, obtain an approved change proposal, then record a new superseding run.
Never overwrite the original run.

For CP-10, keep the immutable run 07 review unchanged. Approval is derived from
the five exact replacement records and the Approved CP-10 document, not by
backfilling `change_proposal_id` into the source.

Use the repeatable `--run-type` filter when validating an intermediate matrix:

```text
python tools/evaluate.py validate --run-type baseline --run-type pressure --run-type wording
python tools/evaluate.py summary --run-type baseline --run-type pressure --run-type wording --format json
```
