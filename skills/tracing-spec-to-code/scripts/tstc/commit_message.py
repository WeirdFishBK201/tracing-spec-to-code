from __future__ import annotations

import re
from typing import Iterable

from .evidence import EvidenceRecord
from .issues import ValidationIssue, sort_issues


_SUBJECT = re.compile(
    r"^[a-z][a-z0-9-]*\([a-z0-9][a-z0-9-]*\): \S(?:.*\S)?$"
)
_TRAILER = re.compile(r"^([A-Za-z][A-Za-z-]*):[ \t]+(\S(?:.*\S)?)$")
_TRAILER_NAMES = {
    "milestone": "Milestone",
    "requirements": "Requirements",
    "change-requests": "Change-Requests",
}


def validate_commit_message(record: EvidenceRecord) -> list[ValidationIssue]:
    """Validate the Git-independent canonical milestone commit draft."""
    issues: list[ValidationIssue] = []

    def invalid(message: str) -> None:
        issues.append(
            ValidationIssue(
                code="COMMIT_MESSAGE_INVALID",
                path=record.plan_path,
                line=record.commit_message_line,
                message=message,
            )
        )

    lines = record.commit_message.splitlines()
    if not lines or not _SUBJECT.fullmatch(lines[0]):
        invalid("commit subject must match type(scope): outcome")
    if len(lines) < 3 or lines[1] != "":
        invalid("commit trailers must follow the subject after one blank line")
        trailer_lines: Iterable[str] = lines[1:]
    else:
        trailer_lines = lines[2:]

    trailers: dict[str, list[str]] = {}
    for line in trailer_lines:
        if not line:
            invalid("commit trailer block cannot contain blank lines")
            continue
        match = _TRAILER.fullmatch(line)
        if not match:
            invalid(f"malformed commit trailer: {line}")
            continue
        key = match.group(1).casefold()
        if key not in _TRAILER_NAMES:
            invalid(f"unknown commit trailer: {match.group(1)}")
            continue
        trailers.setdefault(key, []).append(match.group(2))

    expected = {
        "milestone": record.milestone_name,
        "requirements": ", ".join(record.plan_requirement_ids),
    }
    if record.approved_change_requests:
        expected["change-requests"] = ", ".join(
            record.approved_change_requests
        )
    for key, value in expected.items():
        actual = trailers.get(key, [])
        if actual != [value]:
            invalid(
                f"{_TRAILER_NAMES[key]} trailer must appear exactly once "
                f"and equal: {value}"
            )
    for key in _TRAILER_NAMES:
        if key not in expected and trailers.get(key):
            invalid(f"{_TRAILER_NAMES[key]} trailer is not allowed")
    return sort_issues(issues)
