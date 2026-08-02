from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from pathlib import PurePosixPath

from .evidence import EvidenceRecord
from .issues import ValidationIssue, sort_issues


class GitInspectionError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


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


def _run_git_status(repo_root: Path, *arguments: str) -> int:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *arguments],
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise GitInspectionError(f"cannot run git: {error}") from error
    if result.returncode not in {0, 1}:
        diagnostic = result.stderr.decode("utf-8", errors="replace").strip()
        raise GitInspectionError(
            diagnostic or f"git exited with status {result.returncode}"
        )
    return result.returncode


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


def path_differs_from_head(repo_root: Path, path: str) -> bool:
    root = _validate_git_root(repo_root)
    canonical = _canonical_path(path)
    if canonical is None:
        raise GitInspectionError(f"Git path is not canonical: {path}")
    return bool(
        _run_git(
            root,
            "-c",
            "core.quotePath=false",
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--",
            canonical,
        )
    )


def get_head_commit(repo_root: Path) -> str:
    root = _validate_git_root(repo_root)
    value = _run_git(root, "rev-parse", "HEAD").decode(
        "ascii", errors="strict"
    ).strip()
    if re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value) is None:
        raise GitInspectionError("Git returned an invalid HEAD commit ID")
    return value


def get_commit_parents(repo_root: Path, commit: str) -> tuple[str, ...]:
    root = _validate_git_root(repo_root)
    output = _run_git(root, "rev-list", "--parents", "-n", "1", commit)
    try:
        values = output.decode("ascii", errors="strict").strip().split()
    except UnicodeDecodeError as error:
        raise GitInspectionError("Git returned invalid commit parents") from error
    if not values:
        raise GitInspectionError(f"Git commit does not exist: {commit}")
    return tuple(values[1:])


def get_commit_message(repo_root: Path, commit: str) -> str:
    root = _validate_git_root(repo_root)
    output = _run_git(root, "show", "-s", "--format=%B", commit)
    try:
        return output.decode("utf-8", errors="strict").rstrip("\r\n")
    except UnicodeDecodeError as error:
        raise GitInspectionError("Git commit message is not valid UTF-8") from error


def get_commit_paths(repo_root: Path, commit: str) -> tuple[Path, ...]:
    root = _validate_git_root(repo_root)
    output = _run_git(
        root,
        "-c",
        "core.quotePath=false",
        "diff-tree",
        "--root",
        "--no-commit-id",
        "--name-only",
        "--no-renames",
        "-r",
        "-z",
        commit,
        "--",
    )
    return _parse_nul_paths(output, source="committed")


def validate_authoritative_spec(
    repo_root: Path,
    spec_path: str,
) -> list[ValidationIssue]:
    root = _validate_git_root(repo_root)
    canonical = _canonical_path(spec_path)
    if canonical is None:
        raise GitInspectionError(
            f"authoritative spec path is not canonical: {spec_path}"
        )
    relative = Path(canonical)
    tracked = bool(
        _run_git(
            root,
            "-c",
            "core.quotePath=false",
            "ls-files",
            "--cached",
            "-z",
            "--",
            canonical,
        )
    )
    head_paths = _parse_nul_paths(
        _run_git(
            root,
            "-c",
            "core.quotePath=false",
            "ls-tree",
            "-r",
            "--name-only",
            "-z",
            "HEAD",
            "--",
            canonical,
        ),
        source="HEAD",
    )
    in_head = any(path.as_posix() == canonical for path in head_paths)
    issues: list[ValidationIssue] = []

    def add(code: str, reason: str) -> None:
        issues.append(
            ValidationIssue(
                code=code,
                path=relative,
                line=0,
                message=f"authoritative spec {reason}: {canonical}",
            )
        )

    if not tracked:
        add("SPEC_NOT_TRACKED", "is not tracked by Git")
    if not in_head:
        add("SPEC_NOT_IN_HEAD", "does not exist in recorded HEAD")
    if tracked and in_head:
        if _run_git_status(root, "diff", "--cached", "--quiet", "--", canonical):
            add("SPEC_INDEX_DIRTY", "index differs from recorded HEAD")
        if _run_git_status(root, "diff", "--quiet", "--", canonical):
            add("SPEC_WORKTREE_DIRTY", "worktree differs from the index")
    return sort_issues(issues)
def validate_staged_scope(
    record: EvidenceRecord,
    staged_paths: tuple[Path, ...],
    approved_baseline_ownership_transfers: tuple[str, ...] = (),
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

    approved_transfer_identities = {
        _path_identity(canonical)
        for path in approved_baseline_ownership_transfers
        if (canonical := _canonical_path(path)) is not None
    }
    for path in record.baseline_dirty_paths:
        canonical = _canonical_path(path)
        if (
            canonical is not None
            and _path_identity(canonical) in canonical_scope
            and _path_identity(canonical) not in approved_transfer_identities
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
