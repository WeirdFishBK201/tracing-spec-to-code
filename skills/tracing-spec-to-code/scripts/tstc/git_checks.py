from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from pathlib import PurePosixPath
from typing import Iterable

from .evidence import EvidenceRecord
from .issues import ValidationIssue, sort_issues


class GitInspectionError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


_SUBJECT = re.compile(
    r"^[a-z][a-z0-9-]*\([a-z0-9][a-z0-9-]*\): \S(?:.*\S)?$"
)
_TRAILER = re.compile(r"^([A-Za-z][A-Za-z-]*):[ \t]+(\S(?:.*\S)?)$")
_TRAILER_NAMES = {
    "milestone": "Milestone",
    "requirements": "Requirements",
    "change-requests": "Change-Requests",
}
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")
_INVALID_PATH_CHARS = frozenset("*?[")
_CASE_INSENSITIVE_PATHS = os.name == "nt"


def _canonical_path(value: str) -> str | None:
    if (
        not value
        or value.startswith(":")
        or _WINDOWS_ABSOLUTE.match(value)
        or value.startswith(("/", "\\"))
        or "\\" in value
        or any(character in value for character in _INVALID_PATH_CHARS)
        or value.endswith("/")
    ):
        return None
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None
    pure = PurePosixPath(value)
    if pure.is_absolute() or pure.as_posix() != value:
        return None
    return value


def _path_identity(value: str) -> str:
    return value.casefold() if _CASE_INSENSITIVE_PATHS else value


def _run_git(repo_root: Path, *arguments: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *arguments],
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise GitInspectionError(f"cannot run git: {error}") from error
    if result.returncode:
        diagnostic = result.stderr.decode("utf-8", errors="replace").strip()
        raise GitInspectionError(
            diagnostic or f"git exited with status {result.returncode}"
        )
    return result.stdout


def _issue(
    record: EvidenceRecord,
    code: str,
    line: int,
    message: str,
) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        path=record.plan_path,
        line=line,
        message=message,
    )


def _validate_git_root(repo_root: Path) -> Path:
    root = repo_root.resolve()
    if not root.is_dir():
        raise GitInspectionError(f"repository directory does not exist: {root}")
    top_level_bytes = _run_git(root, "rev-parse", "--show-toplevel")
    try:
        top_level = Path(top_level_bytes.decode("utf-8").strip()).resolve()
    except UnicodeDecodeError as error:
        raise GitInspectionError("Git repository path is not valid UTF-8") from error
    if os.path.normcase(str(top_level)) != os.path.normcase(str(root)):
        raise GitInspectionError(
            f"repository path is not the Git worktree root: {root}"
        )
    return root


def _parse_nul_paths(output: bytes, *, source: str) -> tuple[Path, ...]:
    raw_paths = output.split(b"\0")
    if raw_paths and raw_paths[-1] == b"":
        raw_paths.pop()
    paths: list[Path] = []
    seen: set[str] = set()
    for raw_path in raw_paths:
        try:
            value = raw_path.decode("utf-8")
        except UnicodeDecodeError as error:
            raise GitInspectionError("staged path is not valid UTF-8") from error
        canonical = _canonical_path(value)
        if canonical is None:
            raise GitInspectionError(
                f"Git returned a non-canonical {source} path: {value!r}"
            )
        if canonical in seen:
            raise GitInspectionError(
                f"Git returned a duplicate {source} path: {value}"
            )
        seen.add(canonical)
        paths.append(Path(canonical))
    return tuple(sorted(paths, key=lambda path: path.as_posix().casefold()))


def get_staged_paths(repo_root: Path) -> tuple[Path, ...]:
    root = _validate_git_root(repo_root)
    output = _run_git(
        root,
        "-c",
        "core.quotePath=false",
        "diff",
        "--cached",
        "--no-renames",
        "--name-only",
        "-z",
        "--",
    )
    return _parse_nul_paths(output, source="staged")


def _get_unstaged_paths(repo_root: Path) -> tuple[Path, ...]:
    root = _validate_git_root(repo_root)
    output = _run_git(
        root,
        "-c",
        "core.quotePath=false",
        "diff",
        "--no-renames",
        "--name-only",
        "-z",
        "--",
    )
    return _parse_nul_paths(output, source="unstaged")


def _get_staged_deletions(repo_root: Path) -> tuple[Path, ...]:
    root = _validate_git_root(repo_root)
    output = _run_git(
        root,
        "-c",
        "core.quotePath=false",
        "diff",
        "--cached",
        "--no-renames",
        "--diff-filter=D",
        "--name-only",
        "-z",
        "--",
    )
    return _parse_nul_paths(output, source="staged deletion")


def validate_staged_scope(
    record: EvidenceRecord,
    staged_paths: tuple[Path, ...],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    scope_counts: dict[str, int] = {}
    canonical_scope: dict[str, str] = {}
    for row in record.commit_scope:
        canonical = _canonical_path(row.path)
        if canonical is None:
            diagnostic = (
                "Git pathspec magic is not allowed"
                if row.path.startswith(":")
                else "path is not canonical"
            )
            issues.append(
                _issue(
                    record,
                    "STAGED_SCOPE_INVALID",
                    row.line,
                    (
                        f"invalid commit scope path: {row.path} "
                        f"({diagnostic})"
                    ),
                )
            )
        else:
            identity = _path_identity(canonical)
            scope_counts[identity] = scope_counts.get(identity, 0) + 1
            canonical_scope.setdefault(identity, canonical)
    for row in record.commit_scope:
        canonical = _canonical_path(row.path)
        if (
            canonical is not None
            and scope_counts[_path_identity(canonical)] > 1
        ):
            issues.append(
                _issue(
                    record,
                    "STAGED_SCOPE_INVALID",
                    row.line,
                    f"duplicate commit scope path: {row.path}",
                )
            )

    canonical_staged: dict[str, str] = {}
    staged_counts: dict[str, int] = {}
    for path in staged_paths:
        value = path.as_posix()
        canonical = _canonical_path(value)
        if canonical is None:
            diagnostic = (
                "Git pathspec magic is not allowed"
                if value.startswith(":")
                else "path is not canonical"
            )
            issues.append(
                _issue(
                    record,
                    "STAGED_SCOPE_INVALID",
                    record.commit_scope_line,
                    f"invalid staged path: {value} ({diagnostic})",
                )
            )
        else:
            identity = _path_identity(canonical)
            staged_counts[identity] = staged_counts.get(identity, 0) + 1
            canonical_staged.setdefault(identity, canonical)
    for identity, count in staged_counts.items():
        if count > 1:
            value = canonical_staged[identity]
            issues.append(
                _issue(
                    record,
                    "STAGED_SCOPE_INVALID",
                    record.commit_scope_line,
                    f"duplicate staged path: {value}",
                )
            )

    for path in record.baseline_dirty_paths:
        canonical = _canonical_path(path)
        if (
            canonical is not None
            and _path_identity(canonical) in canonical_scope
        ):
            issues.append(
                _issue(
                    record,
                    "STAGED_SCOPE_INVALID",
                    record.baseline_dirty_paths_line,
                    f"baseline dirty path overlaps commit scope: {path}",
                )
            )
    missing = sorted(
        canonical_scope[identity]
        for identity in canonical_scope.keys() - canonical_staged.keys()
    )
    extra = sorted(
        canonical_staged[identity]
        for identity in canonical_staged.keys() - canonical_scope.keys()
    )
    if missing:
        issues.append(
            _issue(
                record,
                "STAGED_SCOPE_INVALID",
                record.commit_scope_line,
                f"commit scope paths are not staged: {', '.join(missing)}",
            )
        )
    if extra:
        issues.append(
            _issue(
                record,
                "STAGED_SCOPE_INVALID",
                record.commit_scope_line,
                f"staged paths are outside commit scope: {', '.join(extra)}",
            )
        )
    return sort_issues(issues)


def validate_commit_message(
    record: EvidenceRecord,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    def invalid(message: str) -> None:
        issues.append(
            _issue(
                record,
                "COMMIT_MESSAGE_INVALID",
                record.commit_message_line,
                message,
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
        expected["change-requests"] = ", ".join(record.approved_change_requests)
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
