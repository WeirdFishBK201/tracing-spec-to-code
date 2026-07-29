from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from string import Formatter
from typing import Any


DEFAULT_SPEC_FILENAME_TEMPLATE = "{feature}-spec.md"
DEFAULT_ROADMAP_FILENAME_TEMPLATE = "{feature}-roadmap.md"
DEFAULT_MILESTONE_PLAN_FILENAME_TEMPLATE = (
    "{feature}-m{milestone}-{milestone_slug}.md"
)
DEFAULT_CHANGE_PROPOSAL_FILENAME_TEMPLATE = (
    "{feature}-cp{proposal}-{proposal_slug}.md"
)
CONFIG_KEYS = {
    "spec_dir",
    "plan_dir",
    "change_dir",
    "feature_slug",
    "spec_filename_template",
    "roadmap_filename_template",
    "milestone_plan_filename_template",
    "change_proposal_filename_template",
}


@dataclass(frozen=True)
class ResolvedConfig:
    repo_root: Path
    spec_dir: Path
    plan_dir: Path
    change_dir: Path
    feature_slug: str
    spec_filename_template: str
    roadmap_filename_template: str
    milestone_plan_filename_template: str
    change_proposal_filename_template: str


class ConfigError(Exception):
    def __init__(self, code: str, path: Path, message: str) -> None:
        self.code = code
        self.path = path
        self.message = message
        super().__init__(message)


def load_config(
    repo_root: Path,
    config_path: Path | None = None,
) -> ResolvedConfig:
    root = repo_root.resolve()
    if config_path is None:
        path = root / ".tracing-spec-to-code.json"
    elif config_path.is_absolute():
        path = config_path.resolve()
    else:
        path = (root / config_path).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ConfigError(
            "CFG_PATH_OUTSIDE_REPO",
            path,
            "configuration file must be inside the repository",
        ) from error
    if config_path is not None and not path.is_file():
        raise ConfigError(
            "CFG_INVALID_JSON",
            path,
            "explicit configuration file does not exist",
        )
    data: dict[str, Any] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ConfigError(
                "CFG_INVALID_JSON",
                path,
                f"invalid JSON at line {error.lineno}, column {error.colno}",
            ) from error
        except (OSError, UnicodeError) as error:
            raise ConfigError(
                "CFG_INVALID_JSON",
                path,
                f"cannot read UTF-8 JSON: {error}",
            ) from error
        if not isinstance(data, dict):
            raise ConfigError(
                "CFG_INVALID_JSON",
                path,
                "configuration root must be a JSON object",
            )
        unknown_keys = sorted(set(data) - CONFIG_KEYS)
        if unknown_keys:
            raise ConfigError(
                "CFG_UNKNOWN_KEY",
                path,
                f"unknown configuration key: {unknown_keys[0]}",
            )

    def directory(key: str, default: str) -> Path:
        value = data.get(key, default)
        if not isinstance(value, str):
            raise ConfigError(
                "CFG_INVALID_JSON",
                path,
                f"{key} must be a string",
            )
        configured = Path(value)
        if configured.is_absolute():
            raise ConfigError(
                "CFG_PATH_OUTSIDE_REPO",
                path,
                f"{key} must be relative to the repository root",
            )
        resolved = (root / configured).resolve()
        try:
            resolved.relative_to(root)
        except ValueError as error:
            raise ConfigError(
                "CFG_PATH_OUTSIDE_REPO",
                path,
                f"{key} resolves outside the repository root",
            ) from error
        return resolved

    def filename_template(
        key: str,
        default: str,
        allowed_fields: set[str],
        required_fields: set[str],
    ) -> str:
        value = data.get(key, default)
        if (
            not isinstance(value, str)
            or not value.endswith(".md")
            or "/" in value
            or "\\" in value
            or ".." in value
        ):
            raise ConfigError(
                "CFG_TEMPLATE_INVALID",
                path,
                f"{key} must be a Markdown filename template without paths",
            )
        try:
            parsed = list(Formatter().parse(value))
        except ValueError as error:
            raise ConfigError(
                "CFG_TEMPLATE_INVALID",
                path,
                f"{key} contains invalid template syntax",
            ) from error
        fields = {
            field_name
            for _, field_name, _, _ in parsed
            if field_name is not None
        }
        unsupported = sorted(fields - allowed_fields)
        missing = sorted(required_fields - fields)
        has_formatting = any(
            format_spec or conversion
            for _, field_name, format_spec, conversion in parsed
            if field_name is not None
        )
        if unsupported or missing or has_formatting:
            details = []
            if unsupported:
                details.append(f"unsupported placeholder: {unsupported[0]}")
            if missing:
                details.append(f"missing placeholder: {missing[0]}")
            if has_formatting:
                details.append("format specifiers and conversions are not allowed")
            raise ConfigError(
                "CFG_TEMPLATE_INVALID",
                path,
                f"{key} is invalid ({'; '.join(details)})",
            )
        return value

    def feature_slug() -> str:
        value = data.get("feature_slug", root.name)
        if (
            not isinstance(value, str)
            or not value
            or "/" in value
            or "\\" in value
            or ".." in value
        ):
            raise ConfigError(
                "CFG_PATH_OUTSIDE_REPO",
                path,
                "feature_slug must be a non-empty filename-safe value",
            )
        return value

    return ResolvedConfig(
        repo_root=root,
        spec_dir=directory("spec_dir", "docs/specs"),
        plan_dir=directory("plan_dir", "docs/plans"),
        change_dir=directory("change_dir", "docs/changes"),
        feature_slug=feature_slug(),
        spec_filename_template=filename_template(
            "spec_filename_template",
            DEFAULT_SPEC_FILENAME_TEMPLATE,
            {"feature"},
            {"feature"},
        ),
        roadmap_filename_template=filename_template(
            "roadmap_filename_template",
            DEFAULT_ROADMAP_FILENAME_TEMPLATE,
            {"feature"},
            {"feature"},
        ),
        milestone_plan_filename_template=filename_template(
            "milestone_plan_filename_template",
            DEFAULT_MILESTONE_PLAN_FILENAME_TEMPLATE,
            {"feature", "milestone", "milestone_slug"},
            {"feature", "milestone", "milestone_slug"},
        ),
        change_proposal_filename_template=(
            filename_template(
                "change_proposal_filename_template",
                DEFAULT_CHANGE_PROPOSAL_FILENAME_TEMPLATE,
                {"feature", "proposal", "proposal_slug"},
                {"feature", "proposal", "proposal_slug"},
            )
        ),
    )
