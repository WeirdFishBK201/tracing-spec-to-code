from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Sequence

if __package__:
    from .distribution import ManifestEntry, build_manifest
else:
    from distribution import ManifestEntry, build_manifest  # type: ignore[no-redef]


VERIFIED_SKILLS_VERSION = "1.5.21"
SKILL_NAME = "tracing-spec-to-code"
CANONICAL_SOURCE = Path(__file__).resolve().parents[1] / "skills" / SKILL_NAME


def build_command(
    source: str,
    scope: str,
    npx_executable: str,
) -> tuple[str, ...]:
    command = [
        npx_executable,
        "--yes",
        f"skills@{VERIFIED_SKILLS_VERSION}",
        "add",
        source,
        "--skill",
        SKILL_NAME,
        "--agent",
        "codex",
    ]
    if scope == "global":
        command.append("--global")
    elif scope != "project":
        raise ValueError(f"unknown scope: {scope}")
    command.extend(("--copy", "--yes"))
    return tuple(command)


def build_isolated_environment(
    base: Path,
    user_root: Path,
) -> dict[str, str]:
    environment = dict(os.environ)
    environment.update(
        {
            "HOME": str(user_root),
            "USERPROFILE": str(user_root),
            "XDG_CONFIG_HOME": str(user_root / ".config"),
            "XDG_CACHE_HOME": str(user_root / ".cache"),
            "APPDATA": str(user_root / "AppData" / "Roaming"),
        }
    )
    return environment


def expected_target(
    project_root: Path,
    user_root: Path,
    scope: str,
) -> Path:
    if scope == "project":
        return project_root / ".agents" / "skills" / SKILL_NAME
    if scope == "global":
        return user_root / ".agents" / "skills" / SKILL_NAME
    raise ValueError(f"unknown scope: {scope}")


def _distributable_manifest(source: Path) -> tuple[ManifestEntry, ...]:
    return tuple(
        entry
        for entry in build_manifest(source)
        if "__pycache__" not in Path(entry.relative_path).parts
        and Path(entry.relative_path).suffix not in {".pyc", ".pyo"}
    )


def compare_manifests(source: Path, target: Path) -> str | None:
    source_entries = {
        entry.relative_path: entry for entry in _distributable_manifest(source)
    }
    target_entries = {
        entry.relative_path: entry for entry in _distributable_manifest(target)
    }
    for relative_path in sorted(set(source_entries) | set(target_entries)):
        if source_entries.get(relative_path) != target_entries.get(relative_path):
            return f"manifest mismatch: {relative_path} differs"
    return None


def _local_source(source: str) -> str:
    path = Path(source)
    return str(path.resolve()) if path.exists() else source


def run_scope(source: str, scope: str) -> str | None:
    npx_executable = shutil.which("npx")
    if npx_executable is None:
        return f"{scope}: npx executable not found"

    with tempfile.TemporaryDirectory(prefix="verify-npx-install-") as base_name:
        base = Path(base_name)
        project_root = base / "project"
        user_root = base / "user"
        project_root.mkdir()
        user_root.mkdir()
        completed = subprocess.run(
            build_command(_local_source(source), scope, npx_executable),
            cwd=project_root,
            env=build_isolated_environment(base, user_root),
            check=False,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if completed.returncode != 0:
            return f"{scope}: npx exited with status {completed.returncode}"
        target = expected_target(project_root, user_root, scope)
        if not target.is_dir():
            return f"{scope}: installed skill target is missing"
        mismatch = compare_manifests(CANONICAL_SOURCE, target)
        if mismatch is not None:
            return f"{scope}: {mismatch}"
    return None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify a pinned, isolated npx Skill installation."
    )
    parser.add_argument("--source", required=True)
    parser.add_argument(
        "--scope", choices=("project", "global", "all"), default="all"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    scopes = ("project", "global") if arguments.scope == "all" else (arguments.scope,)
    try:
        for scope in scopes:
            failure = run_scope(arguments.source, scope)
            if failure is not None:
                print(f"ERROR {failure}", file=sys.stderr)
                return 1
            print(f"VERIFIED {scope}")
    except Exception as error:
        print(f"ERROR RUNTIME: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
