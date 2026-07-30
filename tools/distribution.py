from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


SKILL_NAME = "tracing-spec-to-code"
_REGISTRY_KEYS = frozenset({"schema_version", "clients"})
_CLIENT_KEYS = frozenset(
    {
        "id",
        "display_name",
        "level",
        "project_path",
        "user_path",
        "verification",
    }
)
_VERIFICATION_BY_LEVEL = {
    1: "install-discovery",
    2: "structure-smoke",
}
_CLIENT_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_INVALID_PORTABLE_PATH_CHARACTERS = frozenset('<>:"\\|?*')
_RUNTIME_CACHE_SUFFIXES = frozenset({".pyc", ".pyo"})
_WINDOWS_RESERVED_NAMES = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{number}" for number in range(1, 10)),
        *(f"LPT{number}" for number in range(1, 10)),
    }
)


@dataclass(frozen=True, slots=True)
class ClientSpec:
    id: str
    display_name: str
    level: int
    project_path: str
    user_path: str
    verification: str


@dataclass(frozen=True, slots=True)
class ManifestEntry:
    relative_path: str
    size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class InstallResult:
    client_id: str
    scope: str
    target: Path
    file_count: int


@dataclass(frozen=True, slots=True)
class _TreeSnapshot:
    directories: tuple[str, ...]
    files: tuple[ManifestEntry, ...]


@dataclass(frozen=True, slots=True)
class _DirectoryPin:
    path: Path
    identity: tuple[int, int]
    snapshot: tuple[int, int, int, int, int]


@dataclass(frozen=True, slots=True)
class _OwnedEntry:
    kind: str
    identity: tuple[int, int]


class DistributionError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        path: Path | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.path = path


class _DuplicateKeyError(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _registry_error(path: Path, message: str) -> DistributionError:
    return DistributionError("REGISTRY_INVALID", message, path)


def _require_exact_keys(
    value: dict[str, Any],
    expected: frozenset[str],
    *,
    context: str,
    registry_path: Path,
) -> None:
    actual = frozenset(value)
    if actual == expected:
        return

    details: list[str] = []
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing:
        details.append(f"missing keys: {', '.join(missing)}")
    if unknown:
        details.append(f"unknown keys: {', '.join(unknown)}")
    raise _registry_error(
        registry_path,
        f"{context} has invalid schema ({'; '.join(details)})",
    )


def _portable_path_parts(value: object, *, context: str) -> tuple[str, ...]:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context} must be a non-empty string")
    if "\\" in value:
        raise ValueError(f"{context} must use forward slashes")
    if PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute():
        raise ValueError(f"{context} must be relative")

    parts = tuple(value.split("/"))
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"{context} contains an unsafe path component")

    for part in parts:
        if any(ord(character) < 32 for character in part):
            raise ValueError(f"{context} contains a control character")
        if any(character in _INVALID_PORTABLE_PATH_CHARACTERS for character in part):
            raise ValueError(f"{context} contains a non-portable character")
        if part.endswith((" ", ".")):
            raise ValueError(f"{context} contains a non-portable component")
        reserved_stem = part.split(".", maxsplit=1)[0].upper()
        if reserved_stem in _WINDOWS_RESERVED_NAMES:
            raise ValueError(f"{context} contains a reserved Windows name")
    return parts


def _parse_client(value: object, registry_path: Path, index: int) -> ClientSpec:
    context = f"clients[{index}]"
    if not isinstance(value, dict):
        raise _registry_error(registry_path, f"{context} must be an object")
    _require_exact_keys(
        value,
        _CLIENT_KEYS,
        context=context,
        registry_path=registry_path,
    )

    client_id = value["id"]
    if not isinstance(client_id, str) or _CLIENT_ID_PATTERN.fullmatch(client_id) is None:
        raise _registry_error(
            registry_path,
            f"{context}.id must be a lowercase portable identifier",
        )

    display_name = value["display_name"]
    if (
        not isinstance(display_name, str)
        or not display_name.strip()
        or display_name != display_name.strip()
    ):
        raise _registry_error(
            registry_path,
            f"{context}.display_name must be a non-empty trimmed string",
        )

    level = value["level"]
    if (
        not isinstance(level, int)
        or isinstance(level, bool)
        or level not in _VERIFICATION_BY_LEVEL
    ):
        raise _registry_error(registry_path, f"{context}.level must be 1 or 2")

    verification = value["verification"]
    if verification != _VERIFICATION_BY_LEVEL[level]:
        raise _registry_error(
            registry_path,
            f"{context}.verification is invalid for level {level}",
        )

    project_path = value["project_path"]
    user_path = value["user_path"]
    try:
        _portable_path_parts(project_path, context=f"{context}.project_path")
        _portable_path_parts(user_path, context=f"{context}.user_path")
    except ValueError as error:
        raise _registry_error(registry_path, str(error)) from error

    return ClientSpec(
        id=client_id,
        display_name=display_name,
        level=level,
        project_path=project_path,
        user_path=user_path,
        verification=verification,
    )


def load_registry(path: Path) -> tuple[ClientSpec, ...]:
    registry_path = Path(path)
    try:
        content = registry_path.read_text(encoding="utf-8")
        data = json.loads(content, object_pairs_hook=_reject_duplicate_keys)
    except (OSError, UnicodeError, json.JSONDecodeError, _DuplicateKeyError) as error:
        raise _registry_error(
            registry_path,
            f"cannot read valid registry JSON: {error}",
        ) from error

    if not isinstance(data, dict):
        raise _registry_error(registry_path, "registry root must be an object")
    _require_exact_keys(
        data,
        _REGISTRY_KEYS,
        context="registry",
        registry_path=registry_path,
    )

    schema_version = data["schema_version"]
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version != 1
    ):
        raise _registry_error(registry_path, "schema_version must be 1")

    raw_clients = data["clients"]
    if not isinstance(raw_clients, list) or not raw_clients:
        raise _registry_error(
            registry_path,
            "clients must be a non-empty array",
        )

    clients = tuple(
        _parse_client(raw_client, registry_path, index)
        for index, raw_client in enumerate(raw_clients)
    )
    seen: set[str] = set()
    for client in clients:
        if client.id in seen:
            raise _registry_error(
                registry_path,
                f"duplicate client id: {client.id}",
            )
        seen.add(client.id)
    return clients


def _is_windows_reparse_point(file_stat: os.stat_result) -> bool:
    attributes = getattr(file_stat, "st_file_attributes", 0)
    reparse_point_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_point_flag)


def _stat_identity(file_stat: os.stat_result) -> tuple[int, int]:
    return file_stat.st_dev, file_stat.st_ino


def _stat_snapshot(
    file_stat: os.stat_result,
) -> tuple[int, int, int, int, int]:
    return (
        file_stat.st_dev,
        file_stat.st_ino,
        file_stat.st_size,
        file_stat.st_mtime_ns,
        file_stat.st_ctime_ns,
    )


def _same_path_and_open_file(
    path_stat: os.stat_result,
    open_stat: os.stat_result,
) -> bool:
    return (
        _stat_identity(path_stat) == _stat_identity(open_stat)
        and path_stat.st_size == open_stat.st_size
        and path_stat.st_mtime_ns == open_stat.st_mtime_ns
    )


def _require_regular_file(file_stat: os.stat_result, path: Path) -> None:
    if (
        not stat.S_ISREG(file_stat.st_mode)
        or _is_windows_reparse_point(file_stat)
    ):
        raise DistributionError(
            "SOURCE_INVALID",
            "source contains a non-regular file",
            path,
        )


def _require_directory_snapshot(
    directory_stat: os.stat_result,
    expected_stat: os.stat_result,
    path: Path,
) -> None:
    if (
        not stat.S_ISDIR(expected_stat.st_mode)
        or _is_windows_reparse_point(expected_stat)
        or not stat.S_ISDIR(directory_stat.st_mode)
        or _is_windows_reparse_point(directory_stat)
        or _stat_snapshot(directory_stat) != _stat_snapshot(expected_stat)
    ):
        raise DistributionError(
            "SOURCE_INVALID",
            "source directory changed while building manifest",
            path,
        )


def _hash_file(
    path: Path,
    expected_stat: os.stat_result,
) -> tuple[int, str]:
    try:
        path_stat_before = os.lstat(path)
        _require_regular_file(path_stat_before, path)
        if _stat_snapshot(path_stat_before) != _stat_snapshot(expected_stat):
            raise DistributionError(
                "SOURCE_INVALID",
                "source file changed before hashing",
                path,
            )

        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as file:
            opened_stat = os.fstat(file.fileno())
            _require_regular_file(opened_stat, path)
            if not _same_path_and_open_file(path_stat_before, opened_stat):
                raise DistributionError(
                    "SOURCE_INVALID",
                    "source file changed while opening",
                    path,
                )

            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                size += len(chunk)
                digest.update(chunk)
            final_open_stat = os.fstat(file.fileno())

        path_stat_after = os.lstat(path)
        _require_regular_file(path_stat_after, path)
    except DistributionError:
        raise
    except OSError as error:
        raise DistributionError(
            "SOURCE_INVALID",
            f"cannot hash source file: {error}",
            path,
        ) from error

    if (
        _stat_snapshot(final_open_stat) != _stat_snapshot(opened_stat)
        or size != final_open_stat.st_size
    ):
        raise DistributionError(
            "SOURCE_INVALID",
            "source file changed while hashing",
            path,
        )
    if not _same_path_and_open_file(path_stat_after, final_open_stat):
        raise DistributionError(
            "SOURCE_INVALID",
            "source file was replaced while hashing",
            path,
        )
    return size, digest.hexdigest()


def _is_runtime_cache_entry(
    path: Path,
    file_stat: os.stat_result,
) -> bool:
    return (
        stat.S_ISDIR(file_stat.st_mode) and path.name == "__pycache__"
    ) or (
        stat.S_ISREG(file_stat.st_mode)
        and path.suffix in _RUNTIME_CACHE_SUFFIXES
    )


def _build_manifest(
    source: Path,
    *,
    ignore_runtime_caches: bool,
) -> tuple[ManifestEntry, ...]:
    source_path = Path(source)
    try:
        source_stat = os.lstat(source_path)
    except OSError as error:
        error_path = Path(error.filename) if error.filename else source_path
        raise DistributionError(
            "SOURCE_INVALID",
            f"cannot inspect source: {error}",
            error_path,
        ) from error
    if (
        not stat.S_ISDIR(source_stat.st_mode)
        or _is_windows_reparse_point(source_stat)
    ):
        raise DistributionError(
            "SOURCE_INVALID",
            "source must be a non-symlink directory",
            source_path,
        )

    entries: list[ManifestEntry] = []
    pending = [(source_path, source_stat)]
    try:
        while pending:
            directory, expected_directory_stat = pending.pop()
            directory_stat = os.lstat(directory)
            _require_directory_snapshot(
                directory_stat,
                expected_directory_stat,
                directory,
            )
            with os.scandir(directory) as children:
                opened_directory_stat = os.lstat(directory)
                _require_directory_snapshot(
                    opened_directory_stat,
                    expected_directory_stat,
                    directory,
                )
                for child in children:
                    child_path = Path(child.path)
                    child_stat = os.lstat(child_path)
                    if (
                        ignore_runtime_caches
                        and _is_runtime_cache_entry(child_path, child_stat)
                    ):
                        continue
                    if (
                        stat.S_ISLNK(child_stat.st_mode)
                        or _is_windows_reparse_point(child_stat)
                    ):
                        raise DistributionError(
                            "SOURCE_INVALID",
                            "source contains a symlink",
                            child_path,
                        )
                    if stat.S_ISDIR(child_stat.st_mode):
                        pending.append((child_path, child_stat))
                        continue
                    if not stat.S_ISREG(child_stat.st_mode):
                        raise DistributionError(
                            "SOURCE_INVALID",
                            "source contains a non-regular file",
                            child_path,
                        )

                    size, sha256 = _hash_file(child_path, child_stat)
                    entries.append(
                        ManifestEntry(
                            relative_path=child_path.relative_to(
                                source_path
                            ).as_posix(),
                            size=size,
                            sha256=sha256,
                        )
                    )
                final_directory_stat = os.lstat(directory)
                _require_directory_snapshot(
                    final_directory_stat,
                    expected_directory_stat,
                    directory,
                )
    except DistributionError:
        raise
    except OSError as error:
        error_path = Path(error.filename) if error.filename else source_path
        raise DistributionError(
            "SOURCE_INVALID",
            f"cannot inspect source: {error}",
            error_path,
        ) from error

    return tuple(sorted(entries, key=lambda entry: entry.relative_path))


def build_manifest(source: Path) -> tuple[ManifestEntry, ...]:
    return _build_manifest(source, ignore_runtime_caches=False)


def resolve_install_target(
    client: ClientSpec,
    scope: str,
    root: Path,
) -> Path:
    if scope == "project":
        configured_path = client.project_path
    elif scope == "user":
        configured_path = client.user_path
    else:
        raise DistributionError(
            "TARGET_INVALID",
            f"unknown install scope: {scope}",
        )

    root_path = Path(root)
    try:
        resolved_root = root_path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise DistributionError(
            "TARGET_INVALID",
            f"cannot resolve explicit root: {error}",
            root_path,
        ) from error
    if not resolved_root.is_dir():
        raise DistributionError(
            "TARGET_INVALID",
            "explicit root must be a directory",
            root_path,
        )

    try:
        parts = _portable_path_parts(
            configured_path,
            context=f"{client.id}.{scope}_path",
        )
    except ValueError as error:
        raise DistributionError(
            "TARGET_INVALID",
            str(error),
            root_path,
        ) from error

    unresolved_target = resolved_root.joinpath(*parts, SKILL_NAME)
    try:
        target = unresolved_target.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        raise DistributionError(
            "TARGET_INVALID",
            f"cannot resolve install target: {error}",
            unresolved_target,
        ) from error
    if not target.is_relative_to(resolved_root):
        raise DistributionError(
            "TARGET_INVALID",
            "install target escapes the explicit root",
            target,
        )
    return target


def _lexists(path: Path) -> bool:
    return os.path.lexists(path)


def _pin_directory(path: Path, code: str) -> _DirectoryPin:
    absolute_path = Path(os.path.abspath(path))
    try:
        resolved_path = absolute_path.resolve(strict=True)
        directory_stat = os.lstat(absolute_path)
    except (OSError, RuntimeError) as error:
        raise DistributionError(
            code,
            f"cannot pin directory: {error}",
            absolute_path,
        ) from error
    if (
        resolved_path != absolute_path
        or not stat.S_ISDIR(directory_stat.st_mode)
        or stat.S_ISLNK(directory_stat.st_mode)
        or _is_windows_reparse_point(directory_stat)
    ):
        raise DistributionError(
            code,
            "directory path is symlinked, reparse-backed, or unsafe",
            absolute_path,
        )
    return _DirectoryPin(
        path=absolute_path,
        identity=_stat_identity(directory_stat),
        snapshot=_stat_snapshot(directory_stat),
    )


def _refresh_directory_pin(
    pin: _DirectoryPin,
    code: str,
    *,
    allow_snapshot_change: bool,
) -> _DirectoryPin:
    current = _pin_directory(pin.path, code)
    if current.identity != pin.identity:
        raise DistributionError(
            code,
            "directory identity changed during installation",
            pin.path,
        )
    if not allow_snapshot_change and current.snapshot != pin.snapshot:
        raise DistributionError(
            code,
            "directory metadata changed during installation",
            pin.path,
        )
    return current


def _build_directory_paths(
    source: Path,
    *,
    ignore_runtime_caches: bool,
) -> tuple[str, ...]:
    source_path = Path(source)
    try:
        source_stat = os.lstat(source_path)
    except OSError as error:
        raise DistributionError(
            "SOURCE_INVALID",
            f"cannot inspect source directory topology: {error}",
            source_path,
        ) from error
    if (
        not stat.S_ISDIR(source_stat.st_mode)
        or stat.S_ISLNK(source_stat.st_mode)
        or _is_windows_reparse_point(source_stat)
    ):
        raise DistributionError(
            "SOURCE_INVALID",
            "source topology root must be a safe directory",
            source_path,
        )

    directories: list[str] = []
    pending = [(source_path, source_stat)]
    try:
        while pending:
            directory, expected_stat = pending.pop()
            _require_directory_snapshot(
                os.lstat(directory),
                expected_stat,
                directory,
            )
            with os.scandir(directory) as children:
                for child in children:
                    child_path = Path(child.path)
                    child_stat = os.lstat(child_path)
                    if (
                        ignore_runtime_caches
                        and _is_runtime_cache_entry(child_path, child_stat)
                    ):
                        continue
                    if (
                        stat.S_ISLNK(child_stat.st_mode)
                        or _is_windows_reparse_point(child_stat)
                    ):
                        raise DistributionError(
                            "SOURCE_INVALID",
                            "source topology contains a symlink or reparse point",
                            child_path,
                        )
                    if stat.S_ISDIR(child_stat.st_mode):
                        directories.append(
                            child_path.relative_to(source_path).as_posix()
                        )
                        pending.append((child_path, child_stat))
                    elif not stat.S_ISREG(child_stat.st_mode):
                        raise DistributionError(
                            "SOURCE_INVALID",
                            "source topology contains a non-regular entry",
                            child_path,
                        )
                _require_directory_snapshot(
                    os.lstat(directory),
                    expected_stat,
                    directory,
                )
    except DistributionError:
        raise
    except OSError as error:
        error_path = Path(error.filename) if error.filename else source_path
        raise DistributionError(
            "SOURCE_INVALID",
            f"cannot inspect source directory topology: {error}",
            error_path,
        ) from error
    return tuple(sorted(directories))


def _build_tree_snapshot(
    source: Path,
    *,
    ignore_runtime_caches: bool = False,
) -> _TreeSnapshot:
    if ignore_runtime_caches:
        manifest_builder = lambda path: _build_manifest(
            path,
            ignore_runtime_caches=True,
        )
    else:
        manifest_builder = build_manifest
    files_before = manifest_builder(source)
    directories = _build_directory_paths(
        source,
        ignore_runtime_caches=ignore_runtime_caches,
    )
    files_after = manifest_builder(source)
    if files_after != files_before:
        raise DistributionError(
            "SOURCE_INVALID",
            "source changed while building tree snapshot",
            Path(source),
        )
    return _TreeSnapshot(directories=directories, files=files_before)


def _tree_path_sets(
    snapshot: _TreeSnapshot,
    prefix: str | None = None,
) -> tuple[set[str], set[str]]:
    def qualify(relative_path: str) -> str:
        if prefix is None:
            return relative_path
        return f"{prefix}/{relative_path}"

    directories = {qualify(path) for path in snapshot.directories}
    if prefix is not None:
        directories.add(prefix)
    files = {qualify(entry.relative_path) for entry in snapshot.files}
    return directories, files


def _scan_cleanup_entries(root: Path) -> dict[str, _OwnedEntry]:
    entries: dict[str, _OwnedEntry] = {}
    pending: list[tuple[Path, str]] = [(root, "")]
    try:
        while pending:
            directory, relative_directory = pending.pop()
            directory_stat = os.lstat(directory)
            if (
                not stat.S_ISDIR(directory_stat.st_mode)
                or stat.S_ISLNK(directory_stat.st_mode)
                or _is_windows_reparse_point(directory_stat)
            ):
                raise DistributionError(
                    "COPY_FAILED",
                    "cleanup tree contains an unsafe directory",
                    directory,
                )
            expected_snapshot = _stat_snapshot(directory_stat)
            with os.scandir(directory) as children:
                for child in children:
                    child_path = Path(child.path)
                    relative_path = (
                        f"{relative_directory}/{child.name}"
                        if relative_directory
                        else child.name
                    )
                    child_stat = os.lstat(child_path)
                    if (
                        stat.S_ISLNK(child_stat.st_mode)
                        or _is_windows_reparse_point(child_stat)
                    ):
                        raise DistributionError(
                            "COPY_FAILED",
                            "cleanup tree contains a symlink or reparse point",
                            child_path,
                        )
                    if stat.S_ISDIR(child_stat.st_mode):
                        entries[relative_path] = _OwnedEntry(
                            "directory",
                            _stat_identity(child_stat),
                        )
                        pending.append((child_path, relative_path))
                    elif stat.S_ISREG(child_stat.st_mode):
                        entries[relative_path] = _OwnedEntry(
                            "file",
                            _stat_identity(child_stat),
                        )
                    else:
                        raise DistributionError(
                            "COPY_FAILED",
                            "cleanup tree contains a non-regular entry",
                            child_path,
                        )
                if _stat_snapshot(os.lstat(directory)) != expected_snapshot:
                    raise DistributionError(
                        "COPY_FAILED",
                        "cleanup tree changed while being inspected",
                        directory,
                    )
    except DistributionError:
        raise
    except OSError as error:
        error_path = Path(error.filename) if error.filename else root
        raise DistributionError(
            "COPY_FAILED",
            f"cannot inspect cleanup tree: {error}",
            error_path,
        ) from error
    return entries


def _remove_owned_tree(
    root: Path,
    root_pin: _DirectoryPin,
    allowed_directories: set[str],
    allowed_files: set[str],
    owned_entries: dict[str, _OwnedEntry] | None = None,
) -> None:
    current_root = _refresh_directory_pin(
        root_pin,
        "COPY_FAILED",
        allow_snapshot_change=True,
    )
    entries = _scan_cleanup_entries(root)
    for relative_path, entry in entries.items():
        allowed = (
            relative_path in allowed_directories
            if entry.kind == "directory"
            else relative_path in allowed_files
        )
        if not allowed:
            raise DistributionError(
                "COPY_FAILED",
                "cleanup tree contains an unowned path",
                root / Path(relative_path),
            )
        if owned_entries is not None:
            expected = owned_entries.get(relative_path)
            if expected != entry:
                raise DistributionError(
                    "COPY_FAILED",
                    "cleanup entry identity is not owned by this invocation",
                    root / Path(relative_path),
                )

    file_entries = sorted(
        (
            (relative_path, entry)
            for relative_path, entry in entries.items()
            if entry.kind == "file"
        ),
        reverse=True,
    )
    directory_entries = sorted(
        (
            (relative_path, entry)
            for relative_path, entry in entries.items()
            if entry.kind == "directory"
        ),
        key=lambda item: (item[0].count("/"), item[0]),
        reverse=True,
    )
    try:
        for relative_path, entry in file_entries:
            path = root.joinpath(*relative_path.split("/"))
            current_stat = os.lstat(path)
            if (
                not stat.S_ISREG(current_stat.st_mode)
                or _is_windows_reparse_point(current_stat)
                or _stat_identity(current_stat) != entry.identity
            ):
                raise DistributionError(
                    "COPY_FAILED",
                    "cleanup file was replaced before removal",
                    path,
                )
            os.unlink(path)
        for relative_path, entry in directory_entries:
            path = root.joinpath(*relative_path.split("/"))
            current_stat = os.lstat(path)
            if (
                not stat.S_ISDIR(current_stat.st_mode)
                or stat.S_ISLNK(current_stat.st_mode)
                or _is_windows_reparse_point(current_stat)
                or _stat_identity(current_stat) != entry.identity
            ):
                raise DistributionError(
                    "COPY_FAILED",
                    "cleanup directory was replaced before removal",
                    path,
                )
            os.rmdir(path)
        _refresh_directory_pin(
            current_root,
            "COPY_FAILED",
            allow_snapshot_change=True,
        )
        os.rmdir(root)
    except DistributionError:
        raise
    except OSError as error:
        error_path = Path(error.filename) if error.filename else root
        raise DistributionError(
            "COPY_FAILED",
            f"cannot remove owned cleanup tree: {error}",
            error_path,
        ) from error


def _attach_cleanup_failures(
    original: BaseException,
    cleanup_failures: list[DistributionError],
) -> None:
    if not cleanup_failures:
        return
    details = "; ".join(
        f"{failure.message} [{failure.path}]"
        for failure in cleanup_failures
    )
    note = f"cleanup failed: {details}"
    if isinstance(original, DistributionError):
        original.message = f"{original.message}; {note}"
        original.args = (original.message,)
    elif hasattr(original, "add_note"):
        original.add_note(note)
    else:
        setattr(original, "cleanup_failure", note)


def _validate_destination_ancestors(
    target: Path,
    relative_path: str,
    target_pin: _DirectoryPin,
    owned_entries: dict[str, _OwnedEntry],
    *,
    include_leaf: bool,
) -> _DirectoryPin:
    current_target = _refresh_directory_pin(
        target_pin,
        "COPY_FAILED",
        allow_snapshot_change=False,
    )
    parts = relative_path.split("/")
    ancestor_count = len(parts) if include_leaf else len(parts) - 1
    for index in range(1, ancestor_count + 1):
        ancestor_relative = "/".join(parts[:index])
        expected = owned_entries.get(ancestor_relative)
        ancestor = target.joinpath(*parts[:index])
        try:
            ancestor_stat = os.lstat(ancestor)
        except OSError as error:
            raise DistributionError(
                "COPY_FAILED",
                f"cannot inspect destination ancestor: {error}",
                ancestor,
            ) from error
        if (
            expected is None
            or expected.kind != "directory"
            or not stat.S_ISDIR(ancestor_stat.st_mode)
            or stat.S_ISLNK(ancestor_stat.st_mode)
            or _is_windows_reparse_point(ancestor_stat)
            or _stat_identity(ancestor_stat) != expected.identity
        ):
            raise DistributionError(
                "COPY_FAILED",
                "destination ancestor changed during publication",
                ancestor,
            )
    return current_target


def _remove_exact_created_file(
    path: Path,
    identity: tuple[int, int],
) -> None:
    try:
        current_stat = os.lstat(path)
    except FileNotFoundError:
        return
    except OSError as error:
        raise DistributionError(
            "COPY_FAILED",
            f"cannot inspect exclusively created file: {error}",
            path,
        ) from error
    if (
        not stat.S_ISREG(current_stat.st_mode)
        or _is_windows_reparse_point(current_stat)
        or _stat_identity(current_stat) != identity
    ):
        raise DistributionError(
            "COPY_FAILED",
            "exclusively created file identity changed before rollback",
            path,
        )
    try:
        os.unlink(path)
    except OSError as error:
        raise DistributionError(
            "COPY_FAILED",
            f"cannot roll back exclusively created file: {error}",
            path,
        ) from error


def _remove_exact_created_directory(
    path: Path,
    identity: tuple[int, int],
) -> None:
    try:
        current_stat = os.lstat(path)
    except FileNotFoundError:
        return
    except OSError as error:
        raise DistributionError(
            "COPY_FAILED",
            f"cannot inspect exclusively created directory: {error}",
            path,
        ) from error
    if (
        not stat.S_ISDIR(current_stat.st_mode)
        or stat.S_ISLNK(current_stat.st_mode)
        or _is_windows_reparse_point(current_stat)
        or _stat_identity(current_stat) != identity
    ):
        raise DistributionError(
            "COPY_FAILED",
            "exclusively created directory identity changed before rollback",
            path,
        )
    try:
        os.rmdir(path)
    except OSError as error:
        raise DistributionError(
            "COPY_FAILED",
            f"cannot roll back exclusively created directory: {error}",
            path,
        ) from error


def _rollback_created_directories(
    created_directories: list[tuple[Path, tuple[int, int]]],
) -> list[DistributionError]:
    failures: list[DistributionError] = []
    for path, identity in reversed(created_directories):
        try:
            _remove_exact_created_directory(path, identity)
        except DistributionError as error:
            failures.append(error)
    return failures


def _ensure_install_parent(
    target_parent: Path,
    root_pin: _DirectoryPin,
) -> tuple[
    _DirectoryPin,
    _DirectoryPin,
    list[tuple[Path, tuple[int, int]]],
]:
    try:
        components = target_parent.relative_to(root_pin.path).parts
    except ValueError as error:
        raise DistributionError(
            "TARGET_INVALID",
            "install parent escapes the pinned explicit root",
            target_parent,
        ) from error

    current_pin = root_pin
    created_parents: list[tuple[Path, tuple[int, int]]] = []
    for component in components:
        root_pin = _refresh_directory_pin(
            root_pin,
            "TARGET_INVALID",
            allow_snapshot_change=False,
        )
        if current_pin.path == root_pin.path:
            current_pin = root_pin
        else:
            current_pin = _refresh_directory_pin(
                current_pin,
                "TARGET_INVALID",
                allow_snapshot_change=False,
            )

        candidate = current_pin.path / component
        created = False
        created_identity: tuple[int, int] | None = None
        cleanup_path: Path | None = None
        try:
            try:
                os.mkdir(candidate)
                created = True
            except FileExistsError:
                pass
            except OSError as error:
                raise DistributionError(
                    "COPY_FAILED",
                    f"cannot create install parent: {error}",
                    candidate,
                ) from error

            try:
                candidate_stat = os.lstat(candidate)
                resolved_candidate = candidate.resolve(strict=True)
            except (OSError, RuntimeError) as error:
                raise DistributionError(
                    "TARGET_INVALID",
                    f"cannot inspect install parent: {error}",
                    candidate,
                ) from error
            if (
                not stat.S_ISDIR(candidate_stat.st_mode)
                or stat.S_ISLNK(candidate_stat.st_mode)
                or _is_windows_reparse_point(candidate_stat)
            ):
                raise DistributionError(
                    "TARGET_INVALID",
                    "install parent is symlinked, reparse-backed, or unsafe",
                    candidate,
                )

            if created:
                created_identity = _stat_identity(candidate_stat)
                cleanup_path = resolved_candidate
            if (
                resolved_candidate != candidate
                or not resolved_candidate.is_relative_to(root_pin.path)
            ):
                raise DistributionError(
                    "TARGET_INVALID",
                    "install parent was diverted outside the explicit root",
                    resolved_candidate,
                )

            refreshed_current = _refresh_directory_pin(
                current_pin,
                "TARGET_INVALID",
                allow_snapshot_change=created,
            )
            if current_pin.path == root_pin.path:
                root_pin = refreshed_current
            else:
                root_pin = _refresh_directory_pin(
                    root_pin,
                    "TARGET_INVALID",
                    allow_snapshot_change=created,
                )
            current_pin = _pin_directory(
                resolved_candidate,
                "TARGET_INVALID",
            )
        except BaseException as original_error:
            rollback_parents = list(created_parents)
            if created_identity is not None and cleanup_path is not None:
                rollback_parents.append(
                    (cleanup_path, created_identity)
                )
            _attach_cleanup_failures(
                original_error,
                _rollback_created_directories(rollback_parents),
            )
            raise
        if created_identity is not None and cleanup_path is not None:
            created_parents.append((cleanup_path, created_identity))

    return root_pin, current_pin, created_parents


def _copy_tree_exclusive(
    staged: Path,
    target: Path,
    snapshot: _TreeSnapshot,
    target_pin: _DirectoryPin,
    owned_entries: dict[str, _OwnedEntry],
) -> _DirectoryPin:
    current_target = target_pin

    for relative_path in sorted(
        snapshot.directories,
        key=lambda path: (path.count("/"), path),
    ):
        current_target = _validate_destination_ancestors(
            target,
            relative_path,
            current_target,
            owned_entries,
            include_leaf=False,
        )
        destination = target.joinpath(*relative_path.split("/"))
        os.mkdir(destination)
        destination_stat = os.lstat(destination)
        if (
            not stat.S_ISDIR(destination_stat.st_mode)
            or stat.S_ISLNK(destination_stat.st_mode)
            or _is_windows_reparse_point(destination_stat)
        ):
            raise DistributionError(
                "COPY_FAILED",
                "published directory is unsafe",
                destination,
            )
        owned_entries[relative_path] = _OwnedEntry(
            "directory",
            _stat_identity(destination_stat),
        )
        current_target = _refresh_directory_pin(
            current_target,
            "COPY_FAILED",
            allow_snapshot_change=True,
        )
        current_target = _validate_destination_ancestors(
            target,
            relative_path,
            current_target,
            owned_entries,
            include_leaf=True,
        )

    publication_files = sorted(
        snapshot.files,
        key=lambda entry: (
            entry.relative_path == "SKILL.md",
            entry.relative_path,
        ),
    )
    for manifest_entry in publication_files:
        relative_path = manifest_entry.relative_path
        current_target = _validate_destination_ancestors(
            target,
            relative_path,
            current_target,
            owned_entries,
            include_leaf=False,
        )
        source_path = staged.joinpath(*relative_path.split("/"))
        destination = target.joinpath(*relative_path.split("/"))
        source_stat = os.lstat(source_path)
        _require_regular_file(source_stat, source_path)
        with source_path.open("rb") as source_file:
            destination_file = destination.open("xb")
            opened_identity: tuple[int, int] | None = None
            try:
                opened_stat = os.fstat(destination_file.fileno())
                opened_identity = _stat_identity(opened_stat)
                owned_entries[relative_path] = _OwnedEntry(
                    "file",
                    opened_identity,
                )
                current_target = _refresh_directory_pin(
                    current_target,
                    "COPY_FAILED",
                    allow_snapshot_change=True,
                )
                current_target = _validate_destination_ancestors(
                    target,
                    relative_path,
                    current_target,
                    owned_entries,
                    include_leaf=False,
                )
                destination_stat = os.lstat(destination)
                if (
                    not stat.S_ISREG(destination_stat.st_mode)
                    or _is_windows_reparse_point(destination_stat)
                    or _stat_identity(destination_stat) != opened_identity
                ):
                    raise DistributionError(
                        "COPY_FAILED",
                        "published file path changed before writing",
                        destination,
                    )
                for chunk in iter(
                    lambda: source_file.read(1024 * 1024),
                    b"",
                ):
                    destination_file.write(chunk)
            except BaseException as original_error:
                destination_file.close()
                if opened_identity is not None:
                    try:
                        _remove_exact_created_file(
                            destination,
                            opened_identity,
                        )
                    except DistributionError as cleanup_error:
                        _attach_cleanup_failures(
                            original_error,
                            [cleanup_error],
                        )
                    finally:
                        owned_entries.pop(relative_path, None)
                raise original_error
            else:
                destination_file.close()
        current_target = _refresh_directory_pin(
            current_target,
            "COPY_FAILED",
            allow_snapshot_change=True,
        )
        current_target = _validate_destination_ancestors(
            target,
            relative_path,
            current_target,
            owned_entries,
            include_leaf=False,
        )
        destination_stat = os.lstat(destination)
        if (
            not stat.S_ISREG(destination_stat.st_mode)
            or _is_windows_reparse_point(destination_stat)
            or _stat_identity(destination_stat)
            != owned_entries[relative_path].identity
        ):
            raise DistributionError(
                "COPY_FAILED",
                "published file identity changed",
                destination,
            )
        current_target = _refresh_directory_pin(
            current_target,
            "COPY_FAILED",
            allow_snapshot_change=True,
        )
    return current_target


def _verification_error(
    message: str,
    target: Path,
    error: BaseException | None = None,
) -> DistributionError:
    failure = DistributionError("VERIFY_FAILED", message, target)
    if error is not None:
        failure.__cause__ = error
    return failure


def install_skill(
    source: Path,
    client: ClientSpec,
    scope: str,
    root: Path,
) -> InstallResult:
    source_path = Path(source)
    source_tree = _build_tree_snapshot(
        source_path,
        ignore_runtime_caches=True,
    )
    source_manifest = source_tree.files
    root_pin = _pin_directory(Path(root), "TARGET_INVALID")
    target = resolve_install_target(client, scope, root)
    if not target.is_relative_to(root_pin.path):
        raise DistributionError(
            "TARGET_INVALID",
            "install target escapes the pinned explicit root",
            target,
        )
    if _lexists(target):
        raise DistributionError(
            "TARGET_EXISTS",
            "install target already exists",
            target,
        )

    root_pin = _refresh_directory_pin(
        root_pin,
        "TARGET_INVALID",
        allow_snapshot_change=False,
    )
    root_pin, parent_pin, created_parents = _ensure_install_parent(
        target.parent,
        root_pin,
    )
    try:
        recomputed_target = resolve_install_target(
            client,
            scope,
            root_pin.path,
        )
        if recomputed_target != target:
            raise DistributionError(
                "TARGET_INVALID",
                "install target changed while creating its parent",
                recomputed_target,
            )

        if _lexists(target):
            raise DistributionError(
                "TARGET_EXISTS",
                "install target already exists",
                target,
            )
    except BaseException as original_error:
        _attach_cleanup_failures(
            original_error,
            _rollback_created_directories(created_parents),
        )
        raise

    workspace: Path | None = None
    workspace_pin: _DirectoryPin | None = None
    workspace_allowed_directories: set[str] = set()
    workspace_allowed_files: set[str] = set()
    workspace_owned_entries: dict[str, _OwnedEntry] = {}
    published_path: Path | None = None
    target_pin: _DirectoryPin | None = None
    target_allowed_directories, target_allowed_files = _tree_path_sets(
        source_tree
    )
    target_owned_entries: dict[str, _OwnedEntry] = {}
    published = False
    try:
        root_pin = _refresh_directory_pin(
            root_pin,
            "TARGET_INVALID",
            allow_snapshot_change=False,
        )
        parent_pin = _refresh_directory_pin(
            parent_pin,
            "TARGET_INVALID",
            allow_snapshot_change=False,
        )
        try:
            raw_workspace = Path(
                tempfile.mkdtemp(
                    prefix=f".{SKILL_NAME}.tmp-",
                    dir=parent_pin.path,
                )
            )
        except OSError as error:
            raise DistributionError(
                "COPY_FAILED",
                f"cannot create installer workspace: {error}",
                target.parent,
            ) from error
        try:
            workspace = raw_workspace.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise DistributionError(
                "COPY_FAILED",
                f"cannot resolve installer workspace: {error}",
                raw_workspace,
            ) from error
        workspace_pin = _pin_directory(workspace, "COPY_FAILED")
        if workspace.parent != parent_pin.path:
            raise DistributionError(
                "TARGET_INVALID",
                "installer workspace was diverted from the pinned parent",
                workspace,
            )
        root_pin = _refresh_directory_pin(
            root_pin,
            "TARGET_INVALID",
            allow_snapshot_change=False,
        )
        parent_pin = _refresh_directory_pin(
            parent_pin,
            "TARGET_INVALID",
            allow_snapshot_change=True,
        )
        staged = workspace / SKILL_NAME
        (
            workspace_allowed_directories,
            workspace_allowed_files,
        ) = _tree_path_sets(source_tree, SKILL_NAME)

        root_pin = _refresh_directory_pin(
            root_pin,
            "TARGET_INVALID",
            allow_snapshot_change=False,
        )
        parent_pin = _refresh_directory_pin(
            parent_pin,
            "TARGET_INVALID",
            allow_snapshot_change=False,
        )
        workspace_pin = _refresh_directory_pin(
            workspace_pin,
            "COPY_FAILED",
            allow_snapshot_change=False,
        )
        staged_owned_entries: dict[str, _OwnedEntry] = {}
        try:
            os.mkdir(staged)
            staged_stat = os.lstat(staged)
            if (
                not stat.S_ISDIR(staged_stat.st_mode)
                or stat.S_ISLNK(staged_stat.st_mode)
                or _is_windows_reparse_point(staged_stat)
            ):
                raise DistributionError(
                    "COPY_FAILED",
                    "staged skill root is unsafe",
                    staged,
                )
            workspace_owned_entries[SKILL_NAME] = _OwnedEntry(
                "directory",
                _stat_identity(staged_stat),
            )
            staged_pin = _pin_directory(staged, "COPY_FAILED")
            _copy_tree_exclusive(
                source_path,
                staged,
                source_tree,
                staged_pin,
                staged_owned_entries,
            )
        except DistributionError:
            raise
        except OSError as error:
            raise DistributionError(
                "COPY_FAILED",
                f"cannot copy canonical skill: {error}",
                target,
            ) from error
        finally:
            workspace_owned_entries.update(
                {
                    f"{SKILL_NAME}/{relative_path}": entry
                    for relative_path, entry in staged_owned_entries.items()
                }
            )
        workspace_pin = _refresh_directory_pin(
            workspace_pin,
            "COPY_FAILED",
            allow_snapshot_change=True,
        )
        root_pin = _refresh_directory_pin(
            root_pin,
            "TARGET_INVALID",
            allow_snapshot_change=False,
        )
        parent_pin = _refresh_directory_pin(
            parent_pin,
            "TARGET_INVALID",
            allow_snapshot_change=False,
        )

        try:
            staged_tree = _build_tree_snapshot(staged)
        except DistributionError as error:
            raise _verification_error(
                f"cannot verify staged copy: {error.message}",
                target,
                error,
            )
        (
            workspace_allowed_directories,
            workspace_allowed_files,
        ) = _tree_path_sets(staged_tree, SKILL_NAME)
        if staged_tree != source_tree:
            raise _verification_error(
                "staged copy does not match canonical source",
                target,
            )

        current_source_tree = _build_tree_snapshot(
            source_path,
            ignore_runtime_caches=True,
        )
        if current_source_tree != source_tree:
            raise DistributionError(
                "SOURCE_INVALID",
                "canonical source changed during installation",
                source_path,
            )

        if _lexists(target):
            raise DistributionError(
                "TARGET_EXISTS",
                "install target already exists",
                target,
            )
        root_pin = _refresh_directory_pin(
            root_pin,
            "TARGET_INVALID",
            allow_snapshot_change=False,
        )
        parent_pin = _refresh_directory_pin(
            parent_pin,
            "TARGET_INVALID",
            allow_snapshot_change=False,
        )
        workspace_pin = _refresh_directory_pin(
            workspace_pin,
            "COPY_FAILED",
            allow_snapshot_change=False,
        )
        try:
            os.mkdir(target)
        except OSError as error:
            if isinstance(error, FileExistsError) or _lexists(target):
                raise DistributionError(
                    "TARGET_EXISTS",
                    "install target already exists",
                    target,
                ) from error
            raise DistributionError(
                "COPY_FAILED",
                f"cannot claim install target: {error}",
                target,
            ) from error
        published = True
        try:
            published_path = target.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise DistributionError(
                "TARGET_INVALID",
                f"cannot resolve claimed install target: {error}",
                target,
            ) from error
        target_pin = _pin_directory(published_path, "TARGET_INVALID")
        if published_path != target:
            raise DistributionError(
                "TARGET_INVALID",
                "claimed install target was diverted from its pinned parent",
                published_path,
            )
        root_pin = _refresh_directory_pin(
            root_pin,
            "TARGET_INVALID",
            allow_snapshot_change=False,
        )
        parent_pin = _refresh_directory_pin(
            parent_pin,
            "TARGET_INVALID",
            allow_snapshot_change=True,
        )
        workspace_pin = _refresh_directory_pin(
            workspace_pin,
            "COPY_FAILED",
            allow_snapshot_change=False,
        )

        try:
            target_pin = _copy_tree_exclusive(
                staged,
                published_path,
                source_tree,
                target_pin,
                target_owned_entries,
            )
        except DistributionError:
            raise
        except OSError as error:
            raise DistributionError(
                "COPY_FAILED",
                f"cannot publish verified skill: {error}",
                target,
            ) from error
        root_pin = _refresh_directory_pin(
            root_pin,
            "TARGET_INVALID",
            allow_snapshot_change=False,
        )
        parent_pin = _refresh_directory_pin(
            parent_pin,
            "TARGET_INVALID",
            allow_snapshot_change=False,
        )
        workspace_pin = _refresh_directory_pin(
            workspace_pin,
            "COPY_FAILED",
            allow_snapshot_change=False,
        )

        try:
            final_tree = _build_tree_snapshot(published_path)
        except DistributionError as error:
            raise _verification_error(
                f"cannot verify installed skill: {error.message}",
                target,
                error,
            )
        if final_tree != source_tree:
            raise _verification_error(
                "installed skill does not match canonical source",
                target,
            )
    except BaseException as original_error:
        cleanup_failures: list[DistributionError] = []
        if (
            published
            and published_path is not None
            and target_pin is not None
            and _lexists(published_path)
        ):
            try:
                _remove_owned_tree(
                    published_path,
                    target_pin,
                    target_allowed_directories,
                    target_allowed_files,
                    target_owned_entries,
                )
            except DistributionError as error:
                cleanup_failures.append(error)
        if (
            workspace is not None
            and workspace_pin is not None
            and _lexists(workspace)
        ):
            try:
                _remove_owned_tree(
                    workspace,
                    workspace_pin,
                    workspace_allowed_directories,
                    workspace_allowed_files,
                    workspace_owned_entries,
                )
            except DistributionError as error:
                cleanup_failures.append(error)
        cleanup_failures.extend(
            _rollback_created_directories(created_parents)
        )
        _attach_cleanup_failures(original_error, cleanup_failures)
        raise

    if workspace is not None and workspace_pin is not None:
        try:
            _remove_owned_tree(
                workspace,
                workspace_pin,
                workspace_allowed_directories,
                workspace_allowed_files,
                workspace_owned_entries,
            )
        except DistributionError as cleanup_error:
            rollback_failures: list[DistributionError] = []
            if (
                published_path is not None
                and target_pin is not None
                and _lexists(published_path)
            ):
                try:
                    _remove_owned_tree(
                        published_path,
                        target_pin,
                        target_allowed_directories,
                        target_allowed_files,
                        target_owned_entries,
                    )
                except DistributionError as error:
                    rollback_failures.append(error)
            rollback_failures.extend(
                _rollback_created_directories(created_parents)
            )
            _attach_cleanup_failures(cleanup_error, rollback_failures)
            raise

    return InstallResult(
        client_id=client.id,
        scope=scope,
        target=target,
        file_count=len(source_manifest),
    )
