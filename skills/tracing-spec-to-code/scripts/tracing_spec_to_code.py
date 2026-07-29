from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from tstc.config import ConfigError
from tstc.validation import validate_repository


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tracing-spec-to-code")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--repo", type=Path, default=Path("."))
    validate_parser.add_argument("--config", type=Path)
    validate_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    repo_root = args.repo.resolve()
    if not repo_root.is_dir():
        print(
            f"repository directory does not exist: {repo_root}",
            file=sys.stderr,
        )
        return 2
    try:
        issues = validate_repository(repo_root, args.config)
    except ConfigError as error:
        print(
            f"{error.code} {error.path}: {error.message}",
            file=sys.stderr,
        )
        return 2
    if args.format == "json":
        print(
            json.dumps(
                {
                    "valid": not issues,
                    "issues": [
                        {
                            "code": issue.code,
                            "path": issue.path.as_posix(),
                            "line": issue.line,
                            "message": issue.message,
                        }
                        for issue in issues
                    ],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 1 if issues else 0
    if issues:
        for issue in issues:
            print(
                f"{issue.code} "
                f"{issue.path.as_posix()}:{issue.line} "
                f"{issue.message}"
            )
        return 1
    print("OK: no validation issues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
