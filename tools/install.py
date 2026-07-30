from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

if __package__:
    from .distribution import (
        DistributionError,
        install_skill,
        load_registry,
    )
else:
    from distribution import (  # type: ignore[no-redef]
        DistributionError,
        install_skill,
        load_registry,
    )


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPOSITORY_ROOT / "tools" / "clients.json"
CANONICAL_SOURCE = REPOSITORY_ROOT / "skills" / "tracing-spec-to-code"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install tracing-spec-to-code into an explicit local root.",
    )
    parser.add_argument("--client", required=True)
    parser.add_argument(
        "--scope",
        required=True,
        choices=("project", "user"),
    )
    roots = parser.add_mutually_exclusive_group()
    roots.add_argument("--project-root", type=Path)
    roots.add_argument("--home-root", type=Path)
    return parser


def _explicit_root(
    parser: argparse.ArgumentParser,
    arguments: argparse.Namespace,
) -> Path:
    if arguments.scope == "project":
        if arguments.project_root is None:
            parser.error("project scope requires --project-root")
        return arguments.project_root
    if arguments.home_root is None:
        parser.error("user scope requires --home-root")
    return arguments.home_root


def _format_policy_error(error: DistributionError) -> str:
    path_suffix = f" [{error.path}]" if error.path is not None else ""
    return f"ERROR {error.code}: {error.message}{path_suffix}"


def _format_runtime_error(error: Exception) -> str:
    cleanup_details = [
        str(note)
        for note in getattr(error, "__notes__", ())
        if str(note)
    ]
    fallback = getattr(error, "cleanup_failure", None)
    if fallback and str(fallback) not in cleanup_details:
        cleanup_details.append(str(fallback))
    suffix = f"; {'; '.join(cleanup_details)}" if cleanup_details else ""
    return f"ERROR RUNTIME: {error}{suffix}"


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    root = _explicit_root(parser, arguments)

    try:
        clients = load_registry(REGISTRY_PATH)
        client = next(
            (item for item in clients if item.id == arguments.client),
            None,
        )
        if client is None:
            raise DistributionError(
                "TARGET_INVALID",
                f"unknown client: {arguments.client}",
            )
        result = install_skill(
            CANONICAL_SOURCE,
            client,
            arguments.scope,
            root,
        )
    except DistributionError as error:
        print(_format_policy_error(error), file=sys.stderr)
        return 1
    except Exception as error:
        print(_format_runtime_error(error), file=sys.stderr)
        return 2

    print(
        f"installed client={result.client_id} scope={result.scope} "
        f"target={result.target} files={result.file_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
