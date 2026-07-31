from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path
from string import Formatter

from .artifacts import ArtifactKind, ArtifactParseError, discover_artifacts
from .config import load_config
from .evidence import parse_evidence, validate_evidence
from .git_checks import (
    GitInspectionError,
    _canonical_path,
    _get_staged_deletions,
    _get_unstaged_paths,
    _path_identity,
    get_staged_paths,
    validate_commit_message,
    validate_staged_scope,
)
from .issues import ValidationIssue, sort_issues
from .validation import validate_repository


class PrecommitRuntimeError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class _ChangeRequestMetadataError(Exception):
    def __init__(self, line: int, message: str) -> None:
        self.line = line
        self.message = message
        super().__init__(message)


_AFFECTED_TASKS = re.compile(
    r"^ {0,3}-[ \t]+(?:Affected[ \t]+tasks|影响[ \t]*Task)"
    r"[ \t]*[:：][ \t]*(.*?)[ \t]*$",
    re.IGNORECASE,
)
_TASK_ID = re.compile(r"M\d{2}-T\d{2}\Z", re.IGNORECASE)
_LEVEL_TWO_HEADING = re.compile(r"^ {0,3}##(?!#)(?:[ \t]+|$)")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


def _without_html_comments(
    line: str,
    in_comment: bool,
) -> tuple[str, bool]:
    visible: list[str] = []
    cursor = 0
    while cursor < len(line):
        if in_comment:
            closing = line.find("-->", cursor)
            if closing < 0:
                return "".join(visible), True
            cursor = closing + 3
            in_comment = False
            continue
        opening = line.find("<!--", cursor)
        if opening < 0:
            visible.append(line[cursor:])
            break
        visible.append(line[cursor:opening])
        cursor = opening + 4
        in_comment = True
    return "".join(visible), in_comment


def _parse_affected_tasks(path: Path) -> tuple[str, ...]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise PrecommitRuntimeError(
            f"cannot read approved change_request metadata: {path}: {error}"
        ) from error

    values: list[tuple[int, str]] = []
    in_comment = False
    fence_character = ""
    fence_length = 0
    for line_number, raw_line in enumerate(lines, start=1):
        line, in_comment = _without_html_comments(raw_line, in_comment)
        if fence_character:
            closing = re.fullmatch(
                rf" {{0,3}}{re.escape(fence_character)}"
                rf"{{{fence_length},}}[ \t]*",
                line,
            )
            if closing:
                fence_character = ""
                fence_length = 0
            continue
        fence = _FENCE.match(line)
        if fence:
            marker = fence.group(1)
            fence_character = marker[0]
            fence_length = len(marker)
            continue
        if _LEVEL_TWO_HEADING.match(line):
            break
        field = _AFFECTED_TASKS.fullmatch(line)
        if field:
            values.append((line_number, field.group(1).strip()))

    if len(values) != 1 or not values[0][1]:
        raise _ChangeRequestMetadataError(
            values[0][0] if values else 1,
            "approved change_request must contain exactly one non-empty "
            "Affected tasks metadata field",
        )
    line_number, value = values[0]
    raw_tasks = re.split(r"[,，]", value)
    if not raw_tasks or any(not value.strip() for value in raw_tasks):
        raise _ChangeRequestMetadataError(
            line_number,
            "approved change_request has invalid Affected tasks metadata",
        )
    tasks = tuple(value.strip().upper() for value in raw_tasks)
    if (
        any(_TASK_ID.fullmatch(task) is None for task in tasks)
        or len(set(tasks)) != len(tasks)
    ):
        raise _ChangeRequestMetadataError(
            line_number,
            "approved change_request has invalid Affected tasks metadata",
        )
    return tuple(sorted(tasks))


def _change_request_id_from_filename(
    filename_template: str,
    feature_slug: str,
    filename: str,
) -> str:
    parts: list[str] = []
    captured_change_request = False
    for literal, field_name, _, _ in Formatter().parse(filename_template):
        parts.append(re.escape(literal))
        if field_name is None:
            continue
        if field_name == "feature":
            parts.append(re.escape(feature_slug))
        elif field_name == "change_request":
            if captured_change_request:
                parts.append(r"(?P=change_request)")
            else:
                parts.append(r"(?P<change_request>\d{2})")
                captured_change_request = True
        elif field_name == "change_request_slug":
            parts.append(r"[A-Za-z0-9][A-Za-z0-9-]*")
    match = re.fullmatch("".join(parts), filename)
    if match is None or not captured_change_request:
        raise PrecommitRuntimeError(
            "cannot derive change_request ID from configured filename template: "
            f"{filename}"
        )
    return f"CR-{int(match.group('change_request')):02d}"


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
    candidate_pairs = [
        (
            artifact,
            _change_request_id_from_filename(
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
        try:
            affected_tasks = _parse_affected_tasks(artifact.path)
        except _ChangeRequestMetadataError as error:
            metadata_invalid = True
            issues.append(
                ValidationIssue(
                    code="EVIDENCE_INCOMPLETE",
                    path=artifact.path.relative_to(root),
                    line=error.line,
                    message=error.message,
                )
            )
            continue
        parsed_candidates.append((artifact, change_request_id, affected_tasks))
    if repository_issues or metadata_invalid:
        unique = {
            (issue.code, issue.path, issue.line, issue.message): issue
            for issue in issues
        }
        return sort_issues(unique.values())

    roadmaps = [
        artifact
        for artifact in artifacts
        if artifact.kind == ArtifactKind.ROADMAP
    ]
    if (
        len(roadmaps) != 1
        or known_plan.milestone_id != roadmaps[0].current_milestone_id
    ):
        raise PrecommitRuntimeError(
            "selected --plan does not match the roadmap current milestone"
        )
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

    require_scope_path(record.plan_path.as_posix())
    for artifact in artifacts:
        if artifact.kind == ArtifactKind.ROADMAP:
            require_scope_path(artifact.path.relative_to(root).as_posix())
    for artifact in approved_change_requests:
        require_scope_path(artifact.path.relative_to(root).as_posix())
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
    try:
        staged_paths = get_staged_paths(root)
        unstaged_paths = _get_unstaged_paths(root)
        staged_deletions = _get_staged_deletions(root)
    except GitInspectionError as error:
        raise PrecommitRuntimeError(error.message) from error
    issues.extend(validate_staged_scope(record, staged_paths))
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
