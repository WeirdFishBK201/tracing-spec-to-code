# CR-01 — Configurable filename templates

- Status: Approved
- Date: 2026-07-30
- Change approval: Approved on 2026-07-30
- Trigger: M01-T01 implementation preflight
- Requirements:REQ-TS2C-001
- Affected milestone: M01 — Artifact contracts
- Affected tasks: M01-T01, M01-T02

## Trigger and evidence

REQ-TS2C-001 requires root-level JSON configuration to override document directories and filename templates, and the design document states that `.tracing-spec-to-code.json` can override both. The approved M01 plan defines `ResolvedConfig` as:

```text
ResolvedConfig(repo_root, spec_dir, plan_dir, change_dir, feature_slug)
```

The interface has no filename-template fields. The planned implementation can therefore override directories only and cannot satisfy the approved specification; extending the interface without a Change approval would silently diverge from the plan.

## Proposed change

Keep M01's three tasks and Python standard-library boundary unchanged, and extend the configuration contract:

```text
ResolvedConfig(
  repo_root,
  spec_dir,
  plan_dir,
  change_dir,
  feature_slug,
  spec_filename_template,
  roadmap_filename_template,
  milestone_plan_filename_template,
  change_request_filename_template,
)
```

Default values:

```text
{feature}-spec.md
{feature}-roadmap.md
{feature}-m{milestone}-{milestone_slug}.md
{feature}-cr{change_request}-{change_request_slug}.md
```

Template rules:

 - A template may generate only one Markdown filename and may not contain an absolute path, directory separator, or `..`.
 - Each template may use only its declared placeholders.
 - spec and roadmap templates must contain `{feature}`.
 - milestone-plan templates must contain `{feature}`, `{milestone}`, and `{milestone_slug}`.
 - change-request templates must contain `{feature}`, `{change_request}`, and `{change_request_slug}`.
 - Invalid templates fail closed through the new stable configuration error code `CFG_TEMPLATE_INVALID`.
 - `discover_artifacts` matches artifact filenames using resolved templates and does not fall back to guessed names.

Required updates:

- M01 plan Interfaces, stable issue codes, T01/T02 test scope, and traceability.
- `assets/templates/config.json` showing all default keys.
- `tests/test_config.py` covering valid overrides, unknown or missing placeholders, path injection, and non-Markdown suffixes.
- `tests/test_artifacts.py` covering discovery with default and custom names.

## Impact

- **Spec**: Unchanged; this delta allows the M01 plan to satisfy REQ-TS2C-001.
- **Roadmap**: Milestone outcomes, dependencies, and requirement coverage remain unchanged.
- **Implementation**: Expand only the planned `config.py` data contract and make `artifacts.py` consume templates.
- **Tests**: Add behavioral tests for filename templates and custom-name discovery.
- **CLI**: Commands, JSON output, and exit codes remain unchanged; template errors still use exit code `2`.
- **Dependencies/network**: No third-party dependency or network access is added.
- **Schedule/scope**: Still three tasks; do not implement Gate workflow, commit automation, or the installer early.

## Alternatives

1. **Change the spec to allow directory overrides only.** Smaller implementation, but it weakens approved REQ-TS2C-001; not recommended.
2. **Defer to a later milestone.** M01 could not claim completion of REQ-TS2C-001; unacceptable.
3. **Allow four specific filenames only.** Simple implementation, but it does not satisfy incremental naming-template semantics for milestones and change requests; not recommended.

## Migration

No released configuration or implementation exists, so no data migration is required. Projects that do not configure these keys continue to use the defaults.

## Change approval

Change approval was approved on 2026-07-30. Update the M01 plan before continuing M01-T01 RED/GREEN.
