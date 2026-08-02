from __future__ import annotations

import re
from dataclasses import dataclass
from string import Formatter
from typing import Sequence

from .markdown_values import parse_markdown_values


@dataclass(frozen=True)
class ChangeRequestMetadata:
    affected_tasks: tuple[str, ...]
    line: int
    authoritative_spec_change: bool | None = None
    authoritative_spec_change_line: int = 0
    fact_change_artifacts: tuple[str, ...] = ()
    fact_change_artifacts_line: int = 0
    fact_change_commit_authorization: str | None = None
    fact_change_commit_authorization_line: int = 0
    fact_change_base_commit: str | None = None
    fact_change_base_commit_line: int = 0
    error: str | None = None


_AFFECTED_TASKS = re.compile(
    r"^ {0,3}-[ \t]+Affected tasks[ \t]*[:：][ \t]*(.*?)[ \t]*$"
)
_AUTHORITATIVE_SPEC_CHANGE = re.compile(
    r"^ {0,3}-[ \t]+Authoritative spec change[ \t]*[:：][ \t]*(.*?)[ \t]*$"
)
_FACT_CHANGE_ARTIFACTS = re.compile(
    r"^ {0,3}-[ \t]+Fact-change artifacts[ \t]*[:：][ \t]*(.*?)[ \t]*$"
)
_FACT_CHANGE_COMMIT_AUTHORIZATION = re.compile(
    r"^ {0,3}-[ \t]+Fact-change commit authorization"
    r"[ \t]*[:：][ \t]*(.*?)[ \t]*$"
)
_FACT_CHANGE_BASE_COMMIT = re.compile(
    r"^ {0,3}-[ \t]+Fact-change base commit[ \t]*[:：][ \t]*(.*?)[ \t]*$"
)
_NONCANONICAL_AFFECTED_TASKS = re.compile(
    r"^ {0,3}-[ \t]+(?P<label>Affected[ \t]+task|影响[ \t]*Task)"
    r"[ \t]*[:：][ \t]*.*$",
    re.IGNORECASE,
)
_TASK_ID = re.compile(r"M\d{2}-T\d{2}\Z")
_LEVEL_TWO_HEADING = re.compile(r"^ {0,3}##(?!#)(?:[ \t]+|$)")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_FULL_COMMIT_ID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


def change_request_id_from_filename(
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
        raise ValueError(
            "cannot derive change_request ID from configured filename template: "
            f"{filename}"
        )
    return f"CR-{int(match.group('change_request')):02d}"


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


def parse_change_request_metadata(
    lines: Sequence[str],
) -> ChangeRequestMetadata:
    values: list[tuple[int, str]] = []
    noncanonical_fields: list[tuple[int, str]] = []
    spec_change_values: list[tuple[int, str]] = []
    artifact_values: list[tuple[int, str]] = []
    authorization_values: list[tuple[int, str]] = []
    base_commit_values: list[tuple[int, str]] = []
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
            continue
        for pattern, destination in (
            (_AUTHORITATIVE_SPEC_CHANGE, spec_change_values),
            (_FACT_CHANGE_ARTIFACTS, artifact_values),
            (_FACT_CHANGE_COMMIT_AUTHORIZATION, authorization_values),
            (_FACT_CHANGE_BASE_COMMIT, base_commit_values),
        ):
            checkpoint_field = pattern.fullmatch(line)
            if checkpoint_field:
                destination.append(
                    (line_number, checkpoint_field.group(1).strip())
                )
                break
        else:
            checkpoint_field = None
        if checkpoint_field is not None:
            continue
        noncanonical = _NONCANONICAL_AFFECTED_TASKS.fullmatch(line)
        if noncanonical:
            noncanonical_fields.append(
                (line_number, noncanonical.group("label"))
            )

    if noncanonical_fields:
        line_number, label = noncanonical_fields[0]
        return ChangeRequestMetadata(
            affected_tasks=(),
            line=line_number,
            error=(
                "Change Request metadata field must be named exactly "
                f"'Affected tasks'; replace '{label}' with 'Affected tasks'"
            ),
        )
    if len(values) != 1:
        return ChangeRequestMetadata(
            affected_tasks=(),
            line=values[1][0] if len(values) > 1 else 1,
            error=(
                "Change Request must contain exactly one canonical "
                "'Affected tasks' metadata field"
            ),
        )
    line_number, value = values[0]
    if not value:
        return ChangeRequestMetadata(
            affected_tasks=(),
            line=line_number,
            error="Change Request 'Affected tasks' metadata value must not be empty",
        )
    raw_tasks = re.split(r"[,，]", value)
    if any(not task.strip() for task in raw_tasks):
        return ChangeRequestMetadata(
            affected_tasks=(),
            line=line_number,
            error=(
                "Change Request 'Affected tasks' must contain comma-separated "
                "task IDs in MNN-TNN format"
            ),
        )
    tasks = tuple(task.strip() for task in raw_tasks)
    if any(_TASK_ID.fullmatch(task) is None for task in tasks):
        return ChangeRequestMetadata(
            affected_tasks=(),
            line=line_number,
            error=(
                "Change Request 'Affected tasks' must contain task IDs in "
                "MNN-TNN format"
            ),
        )
    if len(set(tasks)) != len(tasks):
        return ChangeRequestMetadata(
            affected_tasks=(),
            line=line_number,
            error="Change Request 'Affected tasks' contains duplicate task IDs",
        )
    affected_tasks = tuple(sorted(tasks))
    checkpoint_fields_present = bool(
        artifact_values or authorization_values or base_commit_values
    )
    if not spec_change_values:
        if checkpoint_fields_present:
            return ChangeRequestMetadata(
                affected_tasks=affected_tasks,
                line=line_number,
                error=(
                    "Change Request checkpoint metadata requires exactly one "
                    "canonical 'Authoritative spec change' field"
                ),
            )
        return ChangeRequestMetadata(
            affected_tasks=affected_tasks,
            line=line_number,
        )
    if len(spec_change_values) != 1:
        return ChangeRequestMetadata(
            affected_tasks=affected_tasks,
            line=spec_change_values[1][0],
            error=(
                "Change Request must contain at most one canonical "
                "'Authoritative spec change' field"
            ),
        )
    spec_line, spec_value = spec_change_values[0]
    if spec_value not in {"Yes", "No"}:
        return ChangeRequestMetadata(
            affected_tasks=affected_tasks,
            line=spec_line,
            error="Authoritative spec change must equal exactly 'Yes' or 'No'",
        )
    if spec_value == "No":
        if checkpoint_fields_present:
            return ChangeRequestMetadata(
                affected_tasks=affected_tasks,
                line=spec_line,
                authoritative_spec_change=False,
                authoritative_spec_change_line=spec_line,
                error=(
                    "fact-change checkpoint fields are not allowed when "
                    "Authoritative spec change is No"
                ),
            )
        return ChangeRequestMetadata(
            affected_tasks=affected_tasks,
            line=line_number,
            authoritative_spec_change=False,
            authoritative_spec_change_line=spec_line,
        )

    required = (
        ("Fact-change artifacts", artifact_values),
        ("Fact-change commit authorization", authorization_values),
        ("Fact-change base commit", base_commit_values),
    )
    for label, field_values in required:
        if len(field_values) != 1:
            return ChangeRequestMetadata(
                affected_tasks=affected_tasks,
                line=field_values[1][0] if len(field_values) > 1 else spec_line,
                authoritative_spec_change=True,
                authoritative_spec_change_line=spec_line,
                error=(
                    "approved authoritative spec change requires exactly one "
                    f"canonical '{label}' field"
                ),
            )

    artifacts_line, artifacts_value = artifact_values[0]
    parsed_artifacts = parse_markdown_values(artifacts_value)
    if parsed_artifacts.error is not None or not parsed_artifacts.values:
        return ChangeRequestMetadata(
            affected_tasks=affected_tasks,
            line=artifacts_line,
            authoritative_spec_change=True,
            authoritative_spec_change_line=spec_line,
            error=(
                "Fact-change artifacts must be a non-empty canonical Markdown "
                "value list"
                + (
                    f": {parsed_artifacts.error}"
                    if parsed_artifacts.error is not None
                    else ""
                )
            ),
        )
    authorization_line, authorization = authorization_values[0]
    if authorization not in {"Pending", "Approved", "Rejected"}:
        return ChangeRequestMetadata(
            affected_tasks=affected_tasks,
            line=authorization_line,
            authoritative_spec_change=True,
            authoritative_spec_change_line=spec_line,
            fact_change_artifacts=parsed_artifacts.values,
            fact_change_artifacts_line=artifacts_line,
            error=(
                "Fact-change commit authorization must equal exactly Pending, "
                "Approved, or Rejected"
            ),
        )
    base_line, base_commit = base_commit_values[0]
    if _FULL_COMMIT_ID.fullmatch(base_commit) is None:
        return ChangeRequestMetadata(
            affected_tasks=affected_tasks,
            line=base_line,
            authoritative_spec_change=True,
            authoritative_spec_change_line=spec_line,
            fact_change_artifacts=parsed_artifacts.values,
            fact_change_artifacts_line=artifacts_line,
            fact_change_commit_authorization=authorization,
            fact_change_commit_authorization_line=authorization_line,
            error="Fact-change base commit must be one full lowercase commit ID",
        )
    return ChangeRequestMetadata(
        affected_tasks=affected_tasks,
        line=line_number,
        authoritative_spec_change=True,
        authoritative_spec_change_line=spec_line,
        fact_change_artifacts=parsed_artifacts.values,
        fact_change_artifacts_line=artifacts_line,
        fact_change_commit_authorization=authorization,
        fact_change_commit_authorization_line=authorization_line,
        fact_change_base_commit=base_commit,
        fact_change_base_commit_line=base_line,
    )
