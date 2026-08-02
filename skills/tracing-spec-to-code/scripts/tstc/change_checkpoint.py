from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .artifacts import ArtifactKind, ArtifactParseError, ArtifactRef, discover_artifacts
from .change_requests import change_request_id_from_filename
from .config import load_config
from .git_checks import (
    GitInspectionError,
    _canonical_path,
    _get_staged_deletions,
    _get_unstaged_paths,
    _path_identity,
    get_commit_message,
    get_commit_parents,
    get_commit_paths,
    get_head_commit,
    get_staged_paths,
    validate_authoritative_spec,
)
from .issues import ValidationIssue, sort_issues
from .lifecycle import analyze_milestone_lifecycle
from .validation import validate_repository


class ChangeCheckpointRuntimeError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class ChangeCheckpointContext:
    root: Path
    plan: ArtifactRef
    roadmap: ArtifactRef
    spec: ArtifactRef
    change_request: ArtifactRef
    change_request_id: str
    repository_issues: tuple[ValidationIssue, ...]


@dataclass(frozen=True)
class CheckpointContract:
    expected_paths: dict[str, str]
    expected_message: str
    base_commit: str | None
    issues: tuple[ValidationIssue, ...]


def _issue(
    path: Path,
    line: int,
    code: str,
    message: str,
) -> ValidationIssue:
    return ValidationIssue(code=code, path=path, line=line, message=message)


def _resolve_requested_path(root: Path, requested: Path, label: str) -> Path:
    resolved = requested.resolve() if requested.is_absolute() else (root / requested).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ChangeCheckpointRuntimeError(
            f"selected {label} must be inside the repository"
        ) from error
    return resolved


def _resolve_context(
    repo_root: Path,
    plan_path: Path,
    change_request_path: Path,
    config_path: Path | None,
) -> ChangeCheckpointContext:
    root = repo_root.resolve()
    if not root.is_dir():
        raise ChangeCheckpointRuntimeError(
            f"repository directory does not exist: {root}"
        )
    requested_plan = _resolve_requested_path(root, plan_path, "milestone plan")
    requested_change = _resolve_requested_path(
        root,
        change_request_path,
        "Change Request",
    )
    config = load_config(root, config_path)
    repository_issues = validate_repository(root, config_path)
    try:
        artifacts = discover_artifacts(config)
    except ArtifactParseError as error:
        raise ChangeCheckpointRuntimeError(error.message) from error
    plans = [
        artifact
        for artifact in artifacts
        if artifact.kind == ArtifactKind.MILESTONE_PLAN
        and artifact.path.resolve() == requested_plan
    ]
    changes = [
        artifact
        for artifact in artifacts
        if artifact.kind == ArtifactKind.CHANGE_REQUEST
        and artifact.path.resolve() == requested_change
    ]
    roadmaps = [
        artifact for artifact in artifacts if artifact.kind == ArtifactKind.ROADMAP
    ]
    specs = [artifact for artifact in artifacts if artifact.kind == ArtifactKind.SPEC]
    if len(plans) != 1:
        raise ChangeCheckpointRuntimeError(
            "selected --plan is not an exact discovered milestone plan"
        )
    if len(changes) != 1:
        raise ChangeCheckpointRuntimeError(
            "selected --change-request is not an exact discovered Change Request"
        )
    if len(roadmaps) != 1 or len(specs) != 1:
        raise ChangeCheckpointRuntimeError(
            "checkpoint requires exactly one discovered roadmap and spec"
        )
    lifecycle = analyze_milestone_lifecycle(
        roadmaps[0],
        [
            artifact
            for artifact in artifacts
            if artifact.kind == ArtifactKind.MILESTONE_PLAN
        ],
    )
    if not lifecycle.selected_plan_matches_current(roadmaps[0], plans[0]):
        raise ChangeCheckpointRuntimeError(
            "selected --plan does not match the roadmap current milestone"
        )
    try:
        change_request_id = change_request_id_from_filename(
            config.change_request_filename_template,
            config.feature_slug,
            changes[0].path.name,
        )
    except ValueError as error:
        raise ChangeCheckpointRuntimeError(str(error)) from error
    return ChangeCheckpointContext(
        root=root,
        plan=plans[0],
        roadmap=roadmaps[0],
        spec=specs[0],
        change_request=changes[0],
        change_request_id=change_request_id,
        repository_issues=tuple(repository_issues),
    )


def _checkpoint_contract(
    context: ChangeCheckpointContext,
) -> CheckpointContract:
    root = context.root
    relative_change = context.change_request.path.relative_to(root)
    metadata = context.change_request.change_request_metadata
    issues = list(context.repository_issues)
    approvals = [
        approval
        for approval in context.change_request.approval_refs
        if approval.name == "Change approval"
    ]
    if (
        context.change_request.status != "Approved"
        or len(approvals) != 1
        or approvals[0].status != "Approved"
    ):
        issues.append(
            _issue(
                relative_change,
                approvals[0].line if approvals else context.change_request.status_line,
                "CHANGE_APPROVAL_INVALID",
                "Change Request status and Change approval must both be Approved",
            )
        )
    if (
        metadata is None
        or metadata.error is not None
        or metadata.authoritative_spec_change is not True
    ):
        issues.append(
            _issue(
                relative_change,
                metadata.line if metadata is not None else 1,
                "CHANGE_CHECKPOINT_METADATA_INVALID",
                (
                    metadata.error
                    if metadata is not None and metadata.error is not None
                    else "selected Change Request must declare Authoritative spec change: Yes"
                ),
            )
        )
        return CheckpointContract(
            expected_paths={},
            expected_message=(
                f"docs(change): checkpoint {context.change_request_id} fact change"
            ),
            base_commit=None,
            issues=tuple(sort_issues(issues)),
        )
    if not set(metadata.affected_tasks).intersection(context.plan.task_ids):
        issues.append(
            _issue(
                relative_change,
                metadata.line,
                "CHANGE_CHECKPOINT_METADATA_INVALID",
                "Change Request must affect at least one selected milestone task",
            )
        )
    if metadata.fact_change_commit_authorization != "Approved":
        issues.append(
            _issue(
                relative_change,
                metadata.fact_change_commit_authorization_line or metadata.line,
                "CHANGE_COMMIT_AUTHORIZATION_REQUIRED",
                "fact-change commit requires separate explicit authorization from the current user",
            )
        )

    actual_paths = {
        _path_identity(path.as_posix()): path.as_posix()
        for path in (
            context.spec.path.relative_to(root),
            relative_change,
            context.roadmap.path.relative_to(root),
            context.plan.path.relative_to(root),
        )
    }
    required_identities = {
        _path_identity(context.spec.path.relative_to(root).as_posix()),
        _path_identity(relative_change.as_posix()),
    }
    expected_paths: dict[str, str] = {}
    for value in metadata.fact_change_artifacts:
        canonical = _canonical_path(value)
        if canonical is None:
            issues.append(
                _issue(
                    relative_change,
                    metadata.fact_change_artifacts_line,
                    "CHANGE_CHECKPOINT_METADATA_INVALID",
                    f"invalid fact-change artifact path: {value}",
                )
            )
            continue
        identity = _path_identity(canonical)
        if identity in expected_paths:
            issues.append(
                _issue(
                    relative_change,
                    metadata.fact_change_artifacts_line,
                    "CHANGE_CHECKPOINT_METADATA_INVALID",
                    f"duplicate fact-change artifact identity: {value}",
                )
            )
            continue
        if identity not in actual_paths:
            issues.append(
                _issue(
                    relative_change,
                    metadata.fact_change_artifacts_line,
                    "CHANGE_CHECKPOINT_METADATA_INVALID",
                    "fact-change artifacts may contain only the authoritative spec, "
                    "selected Change Request, current roadmap, and selected plan: "
                    f"{value}",
                )
            )
            continue
        expected_paths[identity] = actual_paths[identity]
    missing_required = sorted(
        actual_paths[identity]
        for identity in required_identities - expected_paths.keys()
    )
    if missing_required:
        issues.append(
            _issue(
                relative_change,
                metadata.fact_change_artifacts_line,
                "CHANGE_CHECKPOINT_METADATA_INVALID",
                "Fact-change artifacts must include: " + ", ".join(missing_required),
            )
        )
    return CheckpointContract(
        expected_paths=expected_paths,
        expected_message=(
            f"docs(change): checkpoint {context.change_request_id} fact change"
        ),
        base_commit=metadata.fact_change_base_commit,
        issues=tuple(sort_issues(issues)),
    )


def _identity_issues(
    context: ChangeCheckpointContext,
    contract: CheckpointContract,
) -> list[ValidationIssue]:
    relative_change = context.change_request.path.relative_to(context.root)
    metadata = context.change_request.change_request_metadata
    line = metadata.fact_change_base_commit_line if metadata is not None else 1
    issues: list[ValidationIssue] = []
    if not contract.expected_paths or contract.base_commit is None:
        return [
            _issue(
                relative_change,
                line,
                "CHANGE_CHECKPOINT_REQUIRED",
                "fact-change checkpoint state is incomplete; task resume is blocked",
            )
        ]
    try:
        head = get_head_commit(context.root)
        parents = get_commit_parents(context.root, head)
        message = get_commit_message(context.root, head)
        committed_paths = get_commit_paths(context.root, head)
    except GitInspectionError as error:
        raise ChangeCheckpointRuntimeError(error.message) from error
    committed = {
        _path_identity(path.as_posix()): path.as_posix()
        for path in committed_paths
    }
    if parents != (contract.base_commit,):
        issues.append(
            _issue(
                relative_change,
                line,
                "CHANGE_CHECKPOINT_REQUIRED",
                "task resume is blocked: HEAD must be exactly one normal "
                "fact-change checkpoint commit "
                f"after recorded base {contract.base_commit}",
            )
        )
    if message != contract.expected_message:
        issues.append(
            _issue(
                relative_change,
                line,
                "CHANGE_CHECKPOINT_REQUIRED",
                "HEAD fact-change checkpoint message must equal: "
                + contract.expected_message,
            )
        )
    if committed.keys() != contract.expected_paths.keys():
        issues.append(
            _issue(
                relative_change,
                line,
                "CHANGE_CHECKPOINT_REQUIRED",
                "HEAD fact-change checkpoint path set must equal metadata scope",
            )
        )
    return issues


def validate_recorded_checkpoint_identity(
    context: ChangeCheckpointContext,
) -> list[ValidationIssue]:
    contract = _checkpoint_contract(context)
    issues = list(contract.issues)
    issues.extend(_identity_issues(context, contract))
    unique = {
        (issue.code, issue.path, issue.line, issue.message): issue
        for issue in issues
    }
    return sort_issues(unique.values())


def validate_change_precommit(
    repo_root: Path,
    plan_path: Path,
    change_request_path: Path,
    message: str,
    config_path: Path | None = None,
) -> list[ValidationIssue]:
    context = _resolve_context(
        repo_root,
        plan_path,
        change_request_path,
        config_path,
    )
    contract = _checkpoint_contract(context)
    issues = list(contract.issues)
    relative_change = context.change_request.path.relative_to(context.root)
    metadata = context.change_request.change_request_metadata
    line = metadata.fact_change_artifacts_line if metadata is not None else 1
    if message != contract.expected_message:
        issues.append(
            _issue(
                relative_change,
                line,
                "CHANGE_MESSAGE_INVALID",
                "fact-change checkpoint message must equal: "
                + contract.expected_message,
            )
        )
    try:
        head = get_head_commit(context.root)
        staged_paths = get_staged_paths(context.root)
        unstaged_paths = _get_unstaged_paths(context.root)
        staged_deletions = _get_staged_deletions(context.root)
        spec_issues = validate_authoritative_spec(
            context.root,
            context.spec.path.relative_to(context.root).as_posix(),
        )
    except GitInspectionError as error:
        raise ChangeCheckpointRuntimeError(error.message) from error
    if contract.base_commit != head:
        issues.append(
            _issue(
                relative_change,
                metadata.fact_change_base_commit_line if metadata is not None else 1,
                "CHANGE_HEAD_INVALID",
                "Fact-change base commit must equal current HEAD before checkpoint",
            )
        )
    staged = {
        _path_identity(path.as_posix()): path.as_posix()
        for path in staged_paths
    }
    missing = sorted(
        contract.expected_paths[identity]
        for identity in contract.expected_paths.keys() - staged.keys()
    )
    extra = sorted(staged[identity] for identity in staged.keys() - contract.expected_paths.keys())
    if missing:
        issues.append(
            _issue(
                relative_change,
                line,
                "CHANGE_SCOPE_INVALID",
                "fact-change artifact paths are not staged: " + ", ".join(missing),
            )
        )
    if extra:
        issues.append(
            _issue(
                relative_change,
                line,
                "CHANGE_SCOPE_INVALID",
                "staged paths are outside fact-change artifact scope: "
                + ", ".join(extra),
            )
        )
    for path in unstaged_paths:
        value = path.as_posix()
        if _path_identity(value) in contract.expected_paths:
            issues.append(
                _issue(
                    Path(value),
                    0,
                    "CHANGE_SCOPE_INVALID",
                    "fact-change artifact has unstaged content: " + value,
                )
            )
    for path in staged_deletions:
        value = path.as_posix()
        if _path_identity(value) in contract.expected_paths:
            issues.append(
                _issue(
                    Path(value),
                    0,
                    "CHANGE_SCOPE_INVALID",
                    "fact-change artifact cannot be deleted: " + value,
                )
            )
    issues.extend(
        issue
        for issue in spec_issues
        if issue.code in {"SPEC_NOT_TRACKED", "SPEC_NOT_IN_HEAD"}
    )
    unique = {
        (issue.code, issue.path, issue.line, issue.message): issue
        for issue in issues
    }
    return sort_issues(unique.values())


def validate_change_resume(
    repo_root: Path,
    plan_path: Path,
    change_request_path: Path,
    config_path: Path | None = None,
) -> list[ValidationIssue]:
    context = _resolve_context(
        repo_root,
        plan_path,
        change_request_path,
        config_path,
    )
    contract = _checkpoint_contract(context)
    issues = list(contract.issues)
    issues.extend(_identity_issues(context, contract))
    try:
        issues.extend(
            validate_authoritative_spec(
                context.root,
                context.spec.path.relative_to(context.root).as_posix(),
            )
        )
        staged = get_staged_paths(context.root)
        unstaged = _get_unstaged_paths(context.root)
    except GitInspectionError as error:
        raise ChangeCheckpointRuntimeError(error.message) from error
    relative_change = context.change_request.path.relative_to(context.root)
    metadata = context.change_request.change_request_metadata
    line = metadata.fact_change_artifacts_line if metadata is not None else 1
    for path in (*staged, *unstaged):
        value = path.as_posix()
        identity = _path_identity(value)
        if (
            identity in contract.expected_paths
            and identity
            != _path_identity(context.spec.path.relative_to(context.root).as_posix())
        ):
            issues.append(
                _issue(
                    relative_change,
                    line,
                    "CHANGE_CHECKPOINT_REQUIRED",
                    "fact-change artifact differs from checkpoint HEAD: " + value,
                )
            )
    unique = {
        (issue.code, issue.path, issue.line, issue.message): issue
        for issue in issues
    }
    return sort_issues(unique.values())


def resolve_change_checkpoint_context(
    repo_root: Path,
    plan_path: Path,
    change_request_path: Path,
    config_path: Path | None = None,
) -> ChangeCheckpointContext:
    return _resolve_context(repo_root, plan_path, change_request_path, config_path)
