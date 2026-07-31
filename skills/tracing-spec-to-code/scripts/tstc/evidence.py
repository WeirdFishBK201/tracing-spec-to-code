from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

from .issues import ValidationIssue, sort_issues


@dataclass(frozen=True)
class TraceabilityRow:
    task_id: str
    requirement_ids: tuple[str, ...]
    implementation: tuple[str, ...]
    tests: tuple[str, ...]
    line: int


@dataclass(frozen=True)
class TaskStatusRow:
    task_id: str
    status: str
    actual_verification: str
    line: int


@dataclass(frozen=True)
class VerificationRow:
    scope: str
    command: str
    expected: str
    actual: str
    result: str
    line: int


@dataclass(frozen=True)
class CommitScopeRow:
    path: str
    purpose: str
    line: int


@dataclass(frozen=True)
class EvidenceRecord:
    plan_path: Path
    milestone_id: str
    traceability: tuple[TraceabilityRow, ...]
    task_statuses: tuple[TaskStatusRow, ...]
    verifications: tuple[VerificationRow, ...]
    approved_change_requests: tuple[str, ...]
    deviations: tuple[str, ...]
    baseline_dirty_paths: tuple[str, ...]
    commit_scope: tuple[CommitScopeRow, ...]
    commit_message: str
    milestone_name: str = ""
    plan_requirement_ids: tuple[str, ...] = ()
    repo_root: Path | None = None
    traceability_table_count: int = 0
    task_status_table_count: int = 0
    verification_table_count: int = 0
    commit_scope_table_count: int = 0
    approved_change_requests_count: int = 0
    deviations_count: int = 0
    baseline_dirty_paths_count: int = 0
    commit_draft_count: int = 0
    approved_change_requests_valid: bool = True
    deviations_valid: bool = True
    baseline_dirty_paths_valid: bool = True
    traceability_line: int = 0
    task_status_line: int = 0
    verification_line: int = 0
    commit_scope_line: int = 0
    approved_change_requests_line: int = 0
    deviations_line: int = 0
    baseline_dirty_paths_line: int = 0
    commit_message_line: int = 0


_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_MILESTONE = re.compile(
    r"^-\s*Milestone\s*[:：]\s*(M\d{2})\b(?:\s*[-–—]\s*(.*?))?\s*$",
    re.IGNORECASE,
)
_REQUIREMENTS = re.compile(
    r"^-\s*Requirements\s*[:：]\s*(.*?)\s*$",
    re.IGNORECASE,
)
_EVIDENCE_FIELD = re.compile(
    r"^-\s*(Approved Change Requests|Deviations|Baseline dirty paths)"
    r"\s*[:：]\s*(.*?)\s*$",
    re.IGNORECASE,
)
_REQUIREMENT_ID = re.compile(r"REQ-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{3}\Z")
_CHANGE_REQUEST_ID = re.compile(r"CR-\d+\Z", re.IGNORECASE)
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")
_INVALID_PATH_CHARS = frozenset("*?[")


def _heading_name(value: str) -> str:
    return re.sub(r"^\d+(?:\.\d+)*\.?\s+", "", value).strip().casefold()


def _table_cells(line: str) -> list[str] | None:
    leading = line[: len(line) - len(line.lstrip())]
    if "\t" in leading or len(leading) > 3:
        return None
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def _is_separator(cells: list[str] | None) -> bool:
    return bool(cells) and all(
        bool(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")))
        for cell in cells
    )


def _clean_cell(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped.startswith("`") and stripped.endswith("`"):
        return stripped[1:-1].strip()
    return stripped


def _split_values(value: str) -> tuple[str, ...]:
    cleaned = _clean_cell(value)
    if not cleaned or cleaned.casefold() == "none":
        return ()
    return tuple(
        item
        for part in cleaned.split(",")
        if (item := _clean_cell(part))
    )


def _parse_table(
    lines: list[str],
    index: int,
) -> tuple[list[str], list[tuple[int, list[str]]], int] | None:
    header = _table_cells(lines[index])
    if header is None or index + 1 >= len(lines):
        return None
    separator = _table_cells(lines[index + 1])
    if not _is_separator(separator) or len(separator or ()) != len(header):
        return None
    rows: list[tuple[int, list[str]]] = []
    cursor = index + 2
    while cursor < len(lines):
        cells = _table_cells(lines[cursor])
        if cells is None or len(cells) != len(header):
            break
        rows.append((cursor + 1, cells))
        cursor += 1
    return (
        [_clean_cell(cell).casefold() for cell in header],
        rows,
        cursor,
    )


def _field_values(value: str) -> tuple[str, ...]:
    return _split_values(value)


def _change_request_values(value: str) -> tuple[tuple[str, ...], bool]:
    if not value.strip():
        return (), False
    values = _field_values(value)
    return (
        tuple(item.upper() for item in values),
        value.strip().casefold() == "none"
        or (
            bool(values)
            and all(_CHANGE_REQUEST_ID.fullmatch(item) for item in values)
        ),
    )


def _evidence_set_values(value: str) -> tuple[tuple[str, ...], bool]:
    stripped = value.strip()
    values = _field_values(value)
    contains_none = any(item.casefold() == "none" for item in values)
    valid = bool(stripped) and (
        stripped.casefold() == "none"
        or (
            bool(values)
            and not contains_none
            and all(
                item.casefold() not in {"pending", "skipped"}
                for item in values
            )
        )
    )
    return values, valid


def _actual_verification_passed(value: str) -> bool:
    match = re.fullmatch(
        r"(?:[A-Za-z0-9_.\-/`]+:\s*)?"
        r"(?:(\d+)/(\d+)\s+)?"
        r"pass(?:ed)?",
        value.strip(),
        re.IGNORECASE,
    )
    if not match:
        return False
    passed, total = match.groups()
    return passed is None or (int(total) > 0 and int(passed) == int(total))


def _fence_opening(line: str) -> tuple[str, int] | None:
    match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
    if not match:
        return None
    marker = match.group(1)
    return marker[0], len(marker)


def _is_fence_closing(line: str, marker: tuple[str, int]) -> bool:
    character, minimum_length = marker
    return bool(
        re.fullmatch(
            rf" {{0,3}}{re.escape(character)}"
            rf"{{{minimum_length},}}\s*",
            line,
        )
    )


def parse_evidence(repo_root: Path, plan_path: Path) -> EvidenceRecord:
    resolved_root = repo_root.resolve()
    resolved_plan = plan_path.resolve()
    relative_path = resolved_plan.relative_to(resolved_root)
    lines = resolved_plan.read_text(encoding="utf-8").splitlines()
    milestone_id = ""
    milestone_name = ""
    plan_requirement_ids: tuple[str, ...] = ()
    traceability: list[TraceabilityRow] = []
    task_statuses: list[TaskStatusRow] = []
    verifications: list[VerificationRow] = []
    approved_change_requests: list[str] = []
    deviations: list[str] = []
    baseline_dirty_paths: list[str] = []
    commit_scope: list[CommitScopeRow] = []
    commit_message = ""

    traceability_table_count = 0
    task_status_table_count = 0
    verification_table_count = 0
    commit_scope_table_count = 0
    approved_change_requests_count = 0
    deviations_count = 0
    baseline_dirty_paths_count = 0
    commit_draft_count = 0
    approved_change_requests_valid = True
    deviations_valid = True
    baseline_dirty_paths_valid = True

    traceability_line = 0
    task_status_line = 0
    verification_line = 0
    commit_scope_line = 0
    approved_change_requests_line = 0
    deviations_line = 0
    baseline_dirty_paths_line = 0
    commit_message_line = 0

    level_two = ""
    level_three = ""
    active_fence: tuple[str, int] | None = None
    in_html_comment = False
    index = 0
    while index < len(lines):
        line = lines[index]

        if active_fence is not None:
            if _is_fence_closing(line, active_fence):
                active_fence = None
            index += 1
            continue

        if in_html_comment:
            if "-->" not in line:
                index += 1
                continue
            _, _, line = line.partition("-->")
            in_html_comment = False
        while "<!--" in line:
            before, _, remainder = line.partition("<!--")
            if "-->" in remainder:
                _, _, after = remainder.partition("-->")
                line = before + after
                continue
            line = before
            in_html_comment = True
            break
        if not line.strip():
            index += 1
            continue

        opening_fence = _fence_opening(line)
        if (
            opening_fence is not None
            and level_two == "evidence and commit"
            and level_three == "commit draft"
        ):
            commit_draft_count += 1
            commit_message_line = commit_message_line or index + 2
            cursor = index + 1
            message_lines: list[str] = []
            while (
                cursor < len(lines)
                and not _is_fence_closing(lines[cursor], opening_fence)
            ):
                message_lines.append(lines[cursor])
                cursor += 1
            if cursor < len(lines) and not commit_message:
                commit_message = "\n".join(message_lines).strip()
            index = cursor + 1
            continue
        if opening_fence is not None:
            active_fence = opening_fence
            index += 1
            continue

        heading = _HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            name = _heading_name(heading.group(2))
            if level == 1:
                level_two = ""
                level_three = ""
            elif level == 2:
                level_two = name
                level_three = ""
            elif level == 3:
                level_three = name
            index += 1
            continue

        if not level_two:
            milestone = _MILESTONE.match(line)
            if milestone and not milestone_id:
                milestone_id = milestone.group(1).upper()
                title = (milestone.group(2) or "").strip()
                milestone_name = (
                    f"{milestone_id} {title}".strip()
                )
            requirements = _REQUIREMENTS.match(line)
            if requirements and not plan_requirement_ids:
                plan_requirement_ids = tuple(
                    value
                    for value in _field_values(requirements.group(1))
                    if _REQUIREMENT_ID.fullmatch(value)
                )

        if level_two == "evidence and commit":
            field = _EVIDENCE_FIELD.match(line)
            if field:
                label = field.group(1).casefold()
                value = field.group(2)
                line_number = index + 1
                if label == "approved change requests":
                    approved_change_requests_count += 1
                    approved_change_requests_line = (
                        approved_change_requests_line or line_number
                    )
                    parsed, valid = _change_request_values(value)
                    approved_change_requests.extend(parsed)
                    approved_change_requests_valid = (
                        approved_change_requests_valid and valid
                    )
                elif label == "deviations":
                    deviations_count += 1
                    deviations_line = deviations_line or line_number
                    parsed, valid = _evidence_set_values(value)
                    deviations.extend(parsed)
                    deviations_valid = deviations_valid and valid
                else:
                    baseline_dirty_paths_count += 1
                    baseline_dirty_paths_line = (
                        baseline_dirty_paths_line or line_number
                    )
                    parsed, valid = _evidence_set_values(value)
                    baseline_dirty_paths.extend(parsed)
                    baseline_dirty_paths_valid = (
                        baseline_dirty_paths_valid and valid
                    )

        parsed_table = _parse_table(lines, index)
        if parsed_table:
            header, rows, next_index = parsed_table
            table_line = index + 1
            if (
                level_two == "traceability"
                and header
                == ["task", "requirements", "implementation", "tests"]
            ):
                traceability_table_count += 1
                traceability_line = traceability_line or table_line
                for line_number, cells in rows:
                    traceability.append(
                        TraceabilityRow(
                            task_id=_clean_cell(cells[0]),
                            requirement_ids=_split_values(cells[1]),
                            implementation=_split_values(cells[2]),
                            tests=_split_values(cells[3]),
                            line=line_number,
                        )
                    )
            elif (
                level_two == "evidence and commit"
                and level_three == "task status"
                and header == ["task", "status", "actual verification"]
            ):
                task_status_table_count += 1
                task_status_line = task_status_line or table_line
                for line_number, cells in rows:
                    task_statuses.append(
                        TaskStatusRow(
                            task_id=_clean_cell(cells[0]),
                            status=_clean_cell(cells[1]),
                            actual_verification=_clean_cell(cells[2]),
                            line=line_number,
                        )
                    )
            elif (
                level_two == "evidence and commit"
                and level_three == "verification"
                and header
                == ["scope", "command", "expected", "actual", "result"]
            ):
                verification_table_count += 1
                verification_line = verification_line or table_line
                for line_number, cells in rows:
                    verifications.append(
                        VerificationRow(
                            scope=_clean_cell(cells[0]),
                            command=_clean_cell(cells[1]),
                            expected=_clean_cell(cells[2]),
                            actual=_clean_cell(cells[3]),
                            result=_clean_cell(cells[4]),
                            line=line_number,
                        )
                    )
            elif (
                level_two == "evidence and commit"
                and level_three == "commit scope"
                and header == ["path", "purpose"]
            ):
                commit_scope_table_count += 1
                commit_scope_line = commit_scope_line or table_line
                for line_number, cells in rows:
                    commit_scope.append(
                        CommitScopeRow(
                            path=_clean_cell(cells[0]),
                            purpose=_clean_cell(cells[1]),
                            line=line_number,
                        )
                    )
            index = next_index
            continue

        index += 1

    return EvidenceRecord(
        plan_path=relative_path,
        milestone_id=milestone_id,
        traceability=tuple(traceability),
        task_statuses=tuple(task_statuses),
        verifications=tuple(verifications),
        approved_change_requests=tuple(approved_change_requests),
        deviations=tuple(deviations),
        baseline_dirty_paths=tuple(baseline_dirty_paths),
        commit_scope=tuple(commit_scope),
        commit_message=commit_message,
        milestone_name=milestone_name,
        plan_requirement_ids=plan_requirement_ids,
        repo_root=resolved_root,
        traceability_table_count=traceability_table_count,
        task_status_table_count=task_status_table_count,
        verification_table_count=verification_table_count,
        commit_scope_table_count=commit_scope_table_count,
        approved_change_requests_count=approved_change_requests_count,
        deviations_count=deviations_count,
        baseline_dirty_paths_count=baseline_dirty_paths_count,
        commit_draft_count=commit_draft_count,
        approved_change_requests_valid=approved_change_requests_valid,
        deviations_valid=deviations_valid,
        baseline_dirty_paths_valid=baseline_dirty_paths_valid,
        traceability_line=traceability_line,
        task_status_line=task_status_line,
        verification_line=verification_line,
        commit_scope_line=commit_scope_line,
        approved_change_requests_line=approved_change_requests_line,
        deviations_line=deviations_line,
        baseline_dirty_paths_line=baseline_dirty_paths_line,
        commit_message_line=commit_message_line,
    )


def _issue(
    record: EvidenceRecord,
    code: str,
    line: int,
    message: str,
) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        path=record.plan_path,
        line=line or 1,
        message=message,
    )


def _counts(values: Iterable[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        result[value] = result.get(value, 0) + 1
    return result


def _task_requirement_ids(known_plan: object) -> dict[str, set[str]]:
    task_requirements: dict[str, set[str]] = {}
    current_task: str | None = None
    section_end_line = 0
    for occurrence in getattr(known_plan, "occurrences", ()):
        if current_task is not None and occurrence.line >= section_end_line:
            current_task = None
        if (
            occurrence.category == "task"
            and occurrence.is_definition
            and occurrence.is_valid
        ):
            current_task = occurrence.value
            section_end_line = occurrence.section_end_line or occurrence.line + 1
            task_requirements.setdefault(current_task, set())
        elif (
            current_task is not None
            and occurrence.category == "requirement"
            and occurrence.is_valid
        ):
            task_requirements[current_task].add(occurrence.value)
    return task_requirements


def _normalized_change_request_id(value: object) -> str | None:
    if isinstance(value, str):
        candidate = value.strip().upper()
        return candidate if _CHANGE_REQUEST_ID.fullmatch(candidate) else None
    path = getattr(value, "path", None)
    if isinstance(path, Path):
        match = re.search(r"(?:^|-)cp0*(\d+)(?:-|$)", path.stem, re.IGNORECASE)
        if match:
            return f"CR-{int(match.group(1)):02d}"
    return None


def _path_error(
    value: str,
    *,
    allow_test_reference: bool = False,
    repo_root: Path | None = None,
) -> str | None:
    path_value = value.split("::", 1)[0] if allow_test_reference else value
    path_value = path_value.strip()
    if not path_value or path_value.casefold() == "none":
        return "path is missing"
    if path_value.startswith(":"):
        return "Git pathspec magic is not allowed"
    if (
        _WINDOWS_ABSOLUTE.match(path_value)
        or path_value.startswith(("/", "\\"))
    ):
        return "absolute paths are not allowed"
    if "\\" in path_value:
        return "path must use normalized repository separators"
    if any(character in path_value for character in _INVALID_PATH_CHARS):
        return "glob paths are not allowed"
    if path_value.endswith("/"):
        return "directory paths are not allowed"
    raw_parts = path_value.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        return "path must be a normalized repository-relative file"
    if PurePosixPath(path_value).is_absolute():
        return "absolute paths are not allowed"
    if repo_root is not None and (repo_root / path_value).is_dir():
        return "directory paths are not allowed"
    return None


def validate_evidence(
    record: EvidenceRecord,
    known_plan: object,
    approved_change_requests: Iterable[object],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    expected_tasks = tuple(getattr(known_plan, "task_ids", ()))
    expected_task_set = set(expected_tasks)
    expected_task_requirements = _task_requirement_ids(known_plan)

    if record.milestone_id != getattr(known_plan, "milestone_id", None):
        issues.append(
            _issue(
                record,
                "EVIDENCE_INCOMPLETE",
                1,
                "evidence milestone does not match the selected plan",
            )
        )
    if record.traceability_table_count != 1:
        issues.append(
            _issue(
                record,
                "EVIDENCE_INCOMPLETE",
                record.traceability_line,
                "exactly one canonical traceability table is required",
            )
        )
    trace_counts = _counts(row.task_id for row in record.traceability)
    for task_id in expected_tasks:
        if trace_counts.get(task_id) != 1:
            issues.append(
                _issue(
                    record,
                    "EVIDENCE_INCOMPLETE",
                    record.traceability_line,
                    f"traceability task must appear exactly once: {task_id}",
                )
            )
    for row in record.traceability:
        if row.task_id not in expected_task_set:
            issues.append(
                _issue(
                    record,
                    "EVIDENCE_INCOMPLETE",
                    row.line,
                    f"unknown traceability task: {row.task_id}",
                )
            )
        row_requirement_set = set(row.requirement_ids)
        if (
            row.task_id in expected_task_set
            and (
                not row.requirement_ids
                or len(row.requirement_ids) != len(row_requirement_set)
                or row_requirement_set
                != expected_task_requirements.get(row.task_id, set())
            )
        ):
            issues.append(
                _issue(
                    record,
                    "EVIDENCE_INCOMPLETE",
                    row.line,
                    (
                        "traceability requirements do not match task section: "
                        f"{row.task_id}"
                    ),
                )
            )
        if not row.implementation:
            issues.append(
                _issue(
                    record,
                    "EVIDENCE_INCOMPLETE",
                    row.line,
                    f"traceability implementation is missing: {row.task_id}",
                )
            )
        for path in row.implementation:
            error = _path_error(path, repo_root=record.repo_root)
            if error:
                issues.append(
                    _issue(
                        record,
                        "EVIDENCE_INCOMPLETE",
                        row.line,
                        f"invalid implementation path {path}: {error}",
                    )
                )
        if not row.tests:
            issues.append(
                _issue(
                    record,
                    "EVIDENCE_INCOMPLETE",
                    row.line,
                    f"traceability tests are missing: {row.task_id}",
                )
            )
        for path in row.tests:
            error = _path_error(
                path,
                allow_test_reference=True,
                repo_root=record.repo_root,
            )
            if error:
                issues.append(
                    _issue(
                        record,
                        "EVIDENCE_INCOMPLETE",
                        row.line,
                        f"invalid test reference {path}: {error}",
                    )
                )

    if record.task_status_table_count != 1:
        issues.append(
            _issue(
                record,
                "EVIDENCE_INCOMPLETE",
                record.task_status_line,
                "exactly one canonical task status table is required",
            )
        )
    status_counts = _counts(row.task_id for row in record.task_statuses)
    for task_id in expected_tasks:
        if status_counts.get(task_id) != 1:
            issues.append(
                _issue(
                    record,
                    "EVIDENCE_INCOMPLETE",
                    record.task_status_line,
                    f"task status must appear exactly once: {task_id}",
                )
            )
    for row in record.task_statuses:
        if row.task_id not in expected_task_set:
            issues.append(
                _issue(
                    record,
                    "EVIDENCE_INCOMPLETE",
                    row.line,
                    f"unknown task status row: {row.task_id}",
                )
            )
        if row.status.casefold() != "completed":
            issues.append(
                _issue(
                    record,
                    "EVIDENCE_INCOMPLETE",
                    row.line,
                    f"task status is not Completed: {row.task_id}",
                )
            )
        if not _actual_verification_passed(row.actual_verification):
            issues.append(
                _issue(
                    record,
                    "EVIDENCE_INCOMPLETE",
                    row.line,
                    f"task status lacks actual verification: {row.task_id}",
                )
            )

    expected_change_requests = {
        change_request_id
        for value in approved_change_requests
        if (change_request_id := _normalized_change_request_id(value))
    }
    recorded_change_requests = set(record.approved_change_requests)
    if (
        record.approved_change_requests_count != 1
        or not record.approved_change_requests_valid
        or len(record.approved_change_requests) != len(recorded_change_requests)
        or recorded_change_requests != expected_change_requests
    ):
        issues.append(
            _issue(
                record,
                "EVIDENCE_INCOMPLETE",
                record.approved_change_requests_line,
                "approved Change Requests evidence does not match approved artifacts",
            )
        )
    if record.deviations_count != 1 or not record.deviations_valid:
        issues.append(
            _issue(
                record,
                "EVIDENCE_INCOMPLETE",
                record.deviations_line,
                "deviations evidence must appear exactly once",
            )
        )
    if (
        record.baseline_dirty_paths_count != 1
        or not record.baseline_dirty_paths_valid
    ):
        issues.append(
            _issue(
                record,
                "EVIDENCE_INCOMPLETE",
                record.baseline_dirty_paths_line,
                "baseline dirty paths evidence must appear exactly once",
            )
        )

    if record.verification_table_count != 1:
        issues.append(
            _issue(
                record,
                "VERIFICATION_NOT_PASSED",
                record.verification_line,
                "exactly one canonical verification table is required",
            )
        )
    passed_scopes: set[str] = set()
    seen_scopes: set[str] = set()
    for row in record.verifications:
        normalized_scope = row.scope.casefold()
        if normalized_scope:
            seen_scopes.add(normalized_scope)
        missing_field = any(
            not value or value.casefold() in {"none", "pending", "skipped"}
            for value in (
                row.scope,
                row.command,
                row.expected,
                row.actual,
                row.result,
            )
        )
        if (
            missing_field
            or row.result.casefold() != "pass"
            or not _actual_verification_passed(row.actual)
        ):
            issues.append(
                _issue(
                    record,
                    "VERIFICATION_NOT_PASSED",
                    row.line,
                    f"verification row is incomplete or not PASS: {row.scope}",
                )
            )
        else:
            passed_scopes.add(normalized_scope)
    for required_scope in ("targeted", "broader"):
        if (
            required_scope not in passed_scopes
            and required_scope not in seen_scopes
        ):
            issues.append(
                _issue(
                    record,
                    "VERIFICATION_NOT_PASSED",
                    record.verification_line,
                    f"required PASS verification is missing: {required_scope}",
                )
            )

    if record.commit_scope_table_count != 1 or not record.commit_scope:
        issues.append(
            _issue(
                record,
                "STAGED_SCOPE_INVALID",
                record.commit_scope_line,
                "exactly one non-empty canonical commit scope table is required",
            )
        )
    scope_counts = _counts(row.path for row in record.commit_scope)
    for row in record.commit_scope:
        error = _path_error(row.path, repo_root=record.repo_root)
        if error:
            issues.append(
                _issue(
                    record,
                    "STAGED_SCOPE_INVALID",
                    row.line,
                    f"invalid commit scope path {row.path}: {error}",
                )
            )
        if scope_counts[row.path] > 1:
            issues.append(
                _issue(
                    record,
                    "STAGED_SCOPE_INVALID",
                    row.line,
                    f"duplicate commit scope path: {row.path}",
                )
            )
        if not row.purpose or row.purpose.casefold() == "none":
            issues.append(
                _issue(
                    record,
                    "STAGED_SCOPE_INVALID",
                    row.line,
                    f"commit scope purpose is missing: {row.path}",
                )
            )
    for path in record.baseline_dirty_paths:
        error = _path_error(path, repo_root=record.repo_root)
        if error:
            issues.append(
                _issue(
                    record,
                    "STAGED_SCOPE_INVALID",
                    record.baseline_dirty_paths_line,
                    f"invalid baseline dirty path {path}: {error}",
                )
            )

    if record.commit_draft_count != 1 or not record.commit_message:
        issues.append(
            _issue(
                record,
                "EVIDENCE_INCOMPLETE",
                record.commit_message_line,
                "exactly one non-empty commit draft is required",
            )
        )
    return sort_issues(issues)
