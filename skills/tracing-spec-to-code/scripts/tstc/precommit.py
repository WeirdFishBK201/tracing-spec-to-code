from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .artifacts import ArtifactKind, ArtifactParseError, discover_artifacts
from .change_checkpoint import (
    resolve_change_checkpoint_context,
    validate_recorded_checkpoint_identity,
)
from .change_requests import change_request_id_from_filename
from .commit_message import validate_commit_message
from .config import load_config
from .evidence import parse_evidence, validate_evidence
from .git_checks import (
    GitInspectionError,
    _canonical_path,
    _get_staged_deletions,
    _get_unstaged_paths,
    _path_identity,
    get_staged_paths,
    path_differs_from_head,
    validate_authoritative_spec,
    validate_staged_scope,
)
from .issues import ValidationIssue, sort_issues
from .lifecycle import analyze_milestone_lifecycle
from .validation import validate_repository


class PrecommitRuntimeError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def validate_precommit(
    repo_root: Path,
    plan_path: Path,
    config_path: Path | None = None,
) -> list[ValidationIssue]:
    root = repo_root.resolve()
    if not root.is_dir():
        raise PrecommitRuntimeError(
            f"repository directory does not exist: {root}"
        )
    requested_plan = (
        plan_path.resolve()
        if plan_path.is_absolute()
        else (root / plan_path).resolve()
    )
    try:
        requested_plan.relative_to(root)
    except ValueError as error:
        raise PrecommitRuntimeError(
            "selected milestone plan must be inside the repository"
        ) from error

    config = load_config(root, config_path)
    repository_issues = validate_repository(root, config_path)
    if any(
        issue.code in {"ARTIFACT_MISSING", "ARTIFACT_PARSE_ERROR"}
        for issue in repository_issues
    ):
        return sort_issues(repository_issues)
    try:
        artifacts = discover_artifacts(config)
    except ArtifactParseError as error:
        return [
            ValidationIssue(
                code=error.code,
                path=error.path.relative_to(root),
                line=error.line,
                message=error.message,
            )
        ]

    plans = [
        artifact
        for artifact in artifacts
        if artifact.kind == ArtifactKind.MILESTONE_PLAN
        and artifact.path.resolve() == requested_plan
    ]
    if len(plans) != 1:
        raise PrecommitRuntimeError(
            "selected --plan is not an exact discovered milestone plan"
        )
    known_plan = plans[0]
    roadmaps = [
        artifact
        for artifact in artifacts
        if artifact.kind == ArtifactKind.ROADMAP
    ]
    discovered_plans = [
        artifact
        for artifact in artifacts
        if artifact.kind == ArtifactKind.MILESTONE_PLAN
    ]
    if len(roadmaps) != 1:
        raise PrecommitRuntimeError(
            "selected --plan does not match the roadmap current milestone"
        )
    lifecycle = analyze_milestone_lifecycle(roadmaps[0], discovered_plans)
    if not lifecycle.selected_plan_matches_current(roadmaps[0], known_plan):
        raise PrecommitRuntimeError(
            "selected --plan does not match the roadmap current milestone"
        )
    approved_candidates = [
        artifact
        for artifact in artifacts
        if artifact.kind == ArtifactKind.CHANGE_REQUEST
        and artifact.status == "Approved"
        and any(
            approval.name.casefold() == "change approval"
            and approval.status == "Approved"
            for approval in artifact.approval_refs
        )
    ]
    issues = list(repository_issues)
    specs = [
        artifact for artifact in artifacts if artifact.kind == ArtifactKind.SPEC
    ]
    expected_spec_path = specs[0].path.relative_to(root).as_posix()
    for referencing_artifact in (roadmaps[0], known_plan):
        if (
            referencing_artifact.spec_path_count != 1
            or _canonical_path(referencing_artifact.spec_path or "")
            != expected_spec_path
        ):
            issues.append(
                ValidationIssue(
                    code="SPEC_PATH_INVALID",
                    path=referencing_artifact.path.relative_to(root),
                    line=referencing_artifact.spec_path_line or 1,
                    message=(
                        "Spec metadata must be the repository-relative "
                        "canonical path to the authoritative spec: "
                        f"{expected_spec_path}"
                    ),
                )
            )
    candidate_pairs = [
        (
            artifact,
            change_request_id_from_filename(
                config.change_request_filename_template,
                config.feature_slug,
                artifact.path.name,
            ),
        )
        for artifact in approved_candidates
    ]
    candidate_ids = [change_request_id for _, change_request_id in candidate_pairs]
    candidate_id_counts = {
        change_request_id: candidate_ids.count(change_request_id)
        for change_request_id in candidate_ids
    }
    for change_request_id in sorted(
        value
        for value, count in candidate_id_counts.items()
        if count > 1
    ):
        duplicate_artifact = next(
            artifact
            for artifact, value in candidate_pairs
            if value == change_request_id
        )
        issues.append(
            ValidationIssue(
                code="EVIDENCE_INCOMPLETE",
                path=duplicate_artifact.path.relative_to(root),
                line=1,
                message=f"duplicate approved Change Request ID: {change_request_id}",
            )
        )

    parsed_candidates = []
    metadata_invalid = False
    for artifact, change_request_id in candidate_pairs:
        metadata = artifact.change_request_metadata
        if metadata is None or metadata.error is not None:
            metadata_invalid = True
            issues.append(
                ValidationIssue(
                    code="EVIDENCE_INCOMPLETE",
                    path=artifact.path.relative_to(root),
                    line=metadata.line if metadata is not None else 1,
                    message=(
                        metadata.error
                        if metadata is not None and metadata.error is not None
                        else "Change Request metadata could not be parsed"
                    ),
                )
            )
            continue
        parsed_candidates.append(
            (artifact, change_request_id, metadata.affected_tasks)
        )
    artifact_gate_codes = {
        "COMMIT_MESSAGE_INVALID",
        "TRACEABILITY_PATH_INVALID",
        "TRACEABILITY_REFERENCE_INVALID",
    }
    blocking_repository_issues = [
        issue
        for issue in repository_issues
        if issue.code not in artifact_gate_codes
    ]
    if blocking_repository_issues or metadata_invalid:
        unique = {
            (issue.code, issue.path, issue.line, issue.message): issue
            for issue in issues
        }
        return sort_issues(unique.values())

    selected_task_ids = set(known_plan.task_ids)
    approved_pairs = [
        (artifact, change_request_id)
        for artifact, change_request_id, affected_tasks in parsed_candidates
        if selected_task_ids.intersection(affected_tasks)
    ]
    approved_change_requests = [artifact for artifact, _ in approved_pairs]
    change_request_ids = [change_request_id for _, change_request_id in approved_pairs]
    approved_change_request_ids = tuple(dict.fromkeys(change_request_ids))
    try:
        record = parse_evidence(root, requested_plan)
    except (OSError, UnicodeError) as error:
        raise PrecommitRuntimeError(
            f"cannot read selected milestone plan: {error}"
        ) from error

    issues.extend(
        validate_evidence(record, known_plan, approved_change_request_ids)
    )
    required_scope_paths: dict[str, str] = {}

    def require_scope_path(value: str) -> None:
        canonical = _canonical_path(value)
        if canonical is not None:
            required_scope_paths.setdefault(
                _path_identity(canonical),
                canonical,
            )

    try:
        if path_differs_from_head(root, record.plan_path.as_posix()):
            require_scope_path(record.plan_path.as_posix())
    except GitInspectionError as error:
        raise PrecommitRuntimeError(error.message) from error
    for artifact in artifacts:
        if artifact.kind == ArtifactKind.ROADMAP:
            relative = artifact.path.relative_to(root).as_posix()
            try:
                if path_differs_from_head(root, relative):
                    require_scope_path(relative)
            except GitInspectionError as error:
                raise PrecommitRuntimeError(error.message) from error
    for artifact in approved_change_requests:
        relative = artifact.path.relative_to(root).as_posix()
        try:
            if path_differs_from_head(root, relative):
                require_scope_path(relative)
        except GitInspectionError as error:
            raise PrecommitRuntimeError(error.message) from error
    for row in record.traceability:
        for value in row.implementation:
            require_scope_path(value)
        for reference in row.tests:
            test_path = reference.split("::", 1)[0]
            require_scope_path(test_path)
    recorded_scope_paths = {
        _path_identity(canonical): canonical
        for row in record.commit_scope
        if (canonical := _canonical_path(row.path)) is not None
    }
    for missing_identity in sorted(
        required_scope_paths.keys() - recorded_scope_paths.keys()
    ):
        missing_path = required_scope_paths[missing_identity]
        issues.append(
            ValidationIssue(
                code="STAGED_SCOPE_INVALID",
                path=record.plan_path,
                line=record.commit_scope_line or 1,
                message=(
                    "required milestone artifact is missing from commit scope: "
                    f"{missing_path}"
                ),
            )
        )
    for artifact, change_request_id in approved_pairs:
        metadata = artifact.change_request_metadata
        if metadata is None or metadata.authoritative_spec_change is not True:
            continue
        context = resolve_change_checkpoint_context(
            root,
            requested_plan,
            artifact.path,
            config_path,
        )
        checkpoint_issues = validate_recorded_checkpoint_identity(context)
        issues.extend(
            issue
            for issue in checkpoint_issues
            if issue.code.startswith("CHANGE_")
            and issue.code != "CHANGE_REQUEST_PENDING"
        )
    roadmap_path = roadmaps[0].path.relative_to(root).as_posix()
    authorized_planning_paths = {
        record.plan_path.as_posix(),
        roadmap_path,
    }
    baseline_paths = set(record.baseline_dirty_paths)
    commit_scope_paths = {
        canonical
        for row in record.commit_scope
        if (canonical := _canonical_path(row.path)) is not None
    }
    approved_transfers: list[str] = []
    for transfer in record.baseline_ownership_transfers:
        canonical = _canonical_path(transfer)
        transfer_valid = True
        if canonical == expected_spec_path:
            transfer_valid = False
            issues.append(
                ValidationIssue(
                    code="SPEC_BASELINE_TRANSFER_FORBIDDEN",
                    path=record.plan_path,
                    line=record.baseline_ownership_transfers_line or 1,
                    message=(
                        "baseline ownership transfer cannot authorize the "
                        f"authoritative spec: {expected_spec_path}"
                    ),
                )
            )
        if canonical is None or canonical not in authorized_planning_paths:
            transfer_valid = False
            issues.append(
                ValidationIssue(
                    code="STAGED_SCOPE_INVALID",
                    path=record.plan_path,
                    line=record.baseline_ownership_transfers_line or 1,
                    message=(
                        "baseline ownership transfer is not authorized for "
                        f"this milestone: {transfer}"
                    ),
                )
            )
        if canonical is None or canonical not in baseline_paths:
            transfer_valid = False
            issues.append(
                ValidationIssue(
                    code="STAGED_SCOPE_INVALID",
                    path=record.plan_path,
                    line=record.baseline_ownership_transfers_line or 1,
                    message=(
                        "baseline ownership transfer is absent from baseline "
                        f"dirty paths: {transfer}"
                    ),
                )
            )
        if canonical is None or canonical not in commit_scope_paths:
            transfer_valid = False
            issues.append(
                ValidationIssue(
                    code="STAGED_SCOPE_INVALID",
                    path=record.plan_path,
                    line=record.baseline_ownership_transfers_line or 1,
                    message=(
                        "baseline ownership transfer is absent from commit "
                        f"scope: {transfer}"
                    ),
                )
            )
        if transfer_valid and canonical is not None:
            approved_transfers.append(canonical)
    try:
        issues.extend(validate_authoritative_spec(root, expected_spec_path))
        staged_paths = get_staged_paths(root)
        unstaged_paths = _get_unstaged_paths(root)
        staged_deletions = _get_staged_deletions(root)
    except GitInspectionError as error:
        raise PrecommitRuntimeError(error.message) from error
    issues.extend(
        validate_staged_scope(
            record,
            staged_paths,
            tuple(approved_transfers),
        )
    )
    scope_lines = {
        _path_identity(canonical): row.line
        for row in record.commit_scope
        if (canonical := _canonical_path(row.path)) is not None
    }
    scoped_unstaged = {
        _path_identity(path.as_posix()): path.as_posix()
        for path in unstaged_paths
        if _path_identity(path.as_posix()) in recorded_scope_paths
    }
    for identity in sorted(scoped_unstaged):
        path = scoped_unstaged[identity]
        issues.append(
            ValidationIssue(
                code="STAGED_SCOPE_INVALID",
                path=record.plan_path,
                line=scope_lines.get(identity, record.commit_scope_line or 1),
                message=(
                    "commit scope path has unstaged content relative to index: "
                    f"{path}"
                ),
            )
        )
    for deletion in staged_deletions:
        value = deletion.as_posix()
        identity = _path_identity(value)
        worktree_path = root / deletion
        if (
            identity in recorded_scope_paths
            and (worktree_path.exists() or worktree_path.is_symlink())
        ):
            issues.append(
                ValidationIssue(
                    code="STAGED_SCOPE_INVALID",
                    path=record.plan_path,
                    line=scope_lines.get(
                        identity,
                        record.commit_scope_line or 1,
                    ),
                    message=(
                        "staged deletion conflicts with a present worktree path: "
                        f"{value}"
                    ),
                )
            )
    issues.extend(
        validate_commit_message(
            replace(
                record,
                approved_change_requests=approved_change_request_ids,
            )
        )
    )

    unique = {
        (issue.code, issue.path, issue.line, issue.message): issue
        for issue in issues
    }
    return sort_issues(unique.values())
