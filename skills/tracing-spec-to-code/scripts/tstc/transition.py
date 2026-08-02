from __future__ import annotations

from pathlib import Path

from .artifacts import ArtifactKind, ArtifactParseError, discover_artifacts
from .config import load_config
from .git_checks import (
    GitInspectionError,
    _canonical_path,
    _get_staged_deletions,
    _get_unstaged_paths,
    _path_identity,
    get_staged_paths,
)
from .issues import ValidationIssue, sort_issues
from .lifecycle import analyze_milestone_lifecycle
from .validation import validate_repository


class TransitionRuntimeError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def _issue(path: Path, line: int, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, path=path, line=line, message=message)


def validate_transition_precommit(
    repo_root: Path,
    plan_path: Path,
    message: str,
    config_path: Path | None = None,
) -> list[ValidationIssue]:
    root = repo_root.resolve()
    if not root.is_dir():
        raise TransitionRuntimeError(
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
        raise TransitionRuntimeError(
            "selected milestone plan must be inside the repository"
        ) from error

    config = load_config(root, config_path)
    repository_issues = validate_repository(root, config_path)
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
    roadmaps = [
        artifact for artifact in artifacts if artifact.kind == ArtifactKind.ROADMAP
    ]
    if len(plans) != 1:
        raise TransitionRuntimeError(
            "selected --plan is not an exact discovered milestone plan"
        )
    if len(roadmaps) != 1:
        raise TransitionRuntimeError(
            "selected --plan does not have exactly one discovered roadmap"
        )

    plan = plans[0]
    roadmap = roadmaps[0]
    relative_plan = plan.path.relative_to(root)
    relative_roadmap = roadmap.path.relative_to(root)
    lifecycle = analyze_milestone_lifecycle(
        roadmap,
        [
            artifact
            for artifact in artifacts
            if artifact.kind == ArtifactKind.MILESTONE_PLAN
        ],
    )
    issues = list(repository_issues)
    expected_roadmap_path = relative_roadmap.as_posix()
    if (
        plan.roadmap_path_count != 1
        or _canonical_path(plan.roadmap_path or "") != expected_roadmap_path
    ):
        issues.append(
            _issue(
                relative_plan,
                plan.roadmap_path_line or 1,
                "LIFECYCLE_STATE_INVALID",
                "Roadmap metadata must identify the one corresponding roadmap: "
                f"{expected_roadmap_path}",
            )
        )

    selected_is_delivered = (
        plan.status == "Delivered"
        and plan.milestone_id == lifecycle.last_closed_milestone_id
        and lifecycle.last_closed_plan_status == "Delivered"
    )
    if not selected_is_delivered:
        issues.append(
            _issue(
                relative_plan,
                plan.status_line or 1,
                "LIFECYCLE_STATE_INVALID",
                "selected plan must be the most recently delivered milestone",
            )
        )

    next_milestone = lifecycle.next_milestone_id
    if next_milestone is None:
        expected_status = "Delivered"
        expected_current = plan.milestone_id
        expected_message = (
            f"chore(plan): record {plan.milestone_id} delivery and close roadmap"
        )
    else:
        expected_status = "Awaiting"
        expected_current = next_milestone
        expected_message = (
            f"chore(plan): record {plan.milestone_id} delivery and advance to "
            f"{next_milestone}"
        )
    if (
        roadmap.status != expected_status
        or roadmap.current_milestone_id != expected_current
    ):
        issues.append(
            _issue(
                relative_roadmap,
                roadmap.status_line or 1,
                "LIFECYCLE_STATE_INVALID",
                "roadmap lifecycle state must be "
                f"Status: {expected_status}, Current milestone: {expected_current}",
            )
        )
    if message != expected_message:
        issues.append(
            _issue(
                relative_plan,
                plan.status_line or 1,
                "LIFECYCLE_MESSAGE_INVALID",
                f"lifecycle checkpoint message must equal: {expected_message}",
            )
        )

    expected_paths = {
        _path_identity(relative_plan.as_posix()): relative_plan.as_posix(),
        _path_identity(relative_roadmap.as_posix()): relative_roadmap.as_posix(),
    }
    try:
        staged_paths = get_staged_paths(root)
        unstaged_paths = _get_unstaged_paths(root)
        staged_deletions = _get_staged_deletions(root)
    except GitInspectionError as error:
        raise TransitionRuntimeError(error.message) from error
    staged = {
        _path_identity(path.as_posix()): path.as_posix()
        for path in staged_paths
    }
    missing = sorted(
        expected_paths[identity]
        for identity in expected_paths.keys() - staged.keys()
    )
    extra = sorted(
        staged[identity] for identity in staged.keys() - expected_paths.keys()
    )
    if missing:
        issues.append(
            _issue(
                relative_plan,
                plan.status_line or 1,
                "LIFECYCLE_SCOPE_INVALID",
                "lifecycle transition paths are not staged: " + ", ".join(missing),
            )
        )
    if extra:
        issues.append(
            _issue(
                relative_plan,
                plan.status_line or 1,
                "LIFECYCLE_SCOPE_INVALID",
                "staged paths are outside lifecycle transition scope: "
                + ", ".join(extra),
            )
        )
    for path in unstaged_paths:
        value = path.as_posix()
        if _path_identity(value) in expected_paths:
            issues.append(
                _issue(
                    Path(value),
                    0,
                    "LIFECYCLE_SCOPE_INVALID",
                    "lifecycle transition path has unstaged content: " + value,
                )
            )
    for path in staged_deletions:
        value = path.as_posix()
        if _path_identity(value) in expected_paths:
            issues.append(
                _issue(
                    Path(value),
                    0,
                    "LIFECYCLE_SCOPE_INVALID",
                    "lifecycle transition path cannot be deleted: " + value,
                )
            )

    unique = {
        (issue.code, issue.path, issue.line, issue.message): issue
        for issue in issues
    }
    return sort_issues(unique.values())
