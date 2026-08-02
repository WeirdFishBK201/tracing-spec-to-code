from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from tstc.change_checkpoint import (
    ChangeCheckpointRuntimeError,
    validate_change_precommit,
    validate_change_resume,
)
from tstc.config import ConfigError
from tstc.precommit import PrecommitRuntimeError, validate_precommit
from tstc.transition import TransitionRuntimeError, validate_transition_precommit
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
    precommit_parser = subparsers.add_parser("precommit")
    precommit_parser.add_argument("--repo", type=Path, default=Path("."))
    precommit_parser.add_argument("--plan", type=Path, required=True)
    precommit_parser.add_argument("--config", type=Path)
    precommit_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
    )
    transition_parser = subparsers.add_parser("transition-precommit")
    transition_parser.add_argument("--repo", type=Path, default=Path("."))
    transition_parser.add_argument("--plan", type=Path, required=True)
    transition_parser.add_argument("--message", required=True)
    transition_parser.add_argument("--config", type=Path)
    transition_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
    )
    change_precommit_parser = subparsers.add_parser("change-precommit")
    change_precommit_parser.add_argument("--repo", type=Path, default=Path("."))
    change_precommit_parser.add_argument("--plan", type=Path, required=True)
    change_precommit_parser.add_argument(
        "--change-request", type=Path, required=True
    )
    change_precommit_parser.add_argument("--message", required=True)
    change_precommit_parser.add_argument("--config", type=Path)
    change_precommit_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
    )
    change_resume_parser = subparsers.add_parser("change-resume")
    change_resume_parser.add_argument("--repo", type=Path, default=Path("."))
    change_resume_parser.add_argument("--plan", type=Path, required=True)
    change_resume_parser.add_argument("--change-request", type=Path, required=True)
    change_resume_parser.add_argument("--config", type=Path)
    change_resume_parser.add_argument(
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
        if args.command == "change-precommit":
            issues = validate_change_precommit(
                repo_root,
                args.plan,
                args.change_request,
                args.message,
                args.config,
            )
        elif args.command == "change-resume":
            issues = validate_change_resume(
                repo_root,
                args.plan,
                args.change_request,
                args.config,
            )
        elif args.command == "precommit":
            issues = validate_precommit(
                repo_root,
                args.plan,
                args.config,
            )
        elif args.command == "transition-precommit":
            issues = validate_transition_precommit(
                repo_root,
                args.plan,
                args.message,
                args.config,
            )
        else:
            issues = validate_repository(repo_root, args.config)
    except ConfigError as error:
        print(
            f"{error.code} {error.path}: {error.message}",
            file=sys.stderr,
        )
        return 2
    except PrecommitRuntimeError as error:
        print(
            f"PRECOMMIT_RUNTIME {error.message}",
            file=sys.stderr,
        )
        return 2
    except TransitionRuntimeError as error:
        print(
            f"TRANSITION_PRECOMMIT_RUNTIME {error.message}",
            file=sys.stderr,
        )
        return 2
    except ChangeCheckpointRuntimeError as error:
        print(
            f"CHANGE_CHECKPOINT_RUNTIME {error.message}",
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
