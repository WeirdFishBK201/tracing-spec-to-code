from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: Path
    line: int
    message: str


def sort_issues(issues: Iterable[ValidationIssue]) -> list[ValidationIssue]:
    return sorted(
        issues,
        key=lambda issue: (
            issue.path.as_posix().casefold(),
            issue.line,
            issue.code,
        ),
    )
