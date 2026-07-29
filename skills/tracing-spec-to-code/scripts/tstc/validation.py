from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .artifacts import ArtifactKind, ArtifactParseError, discover_artifacts
from .config import load_config


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: Path
    line: int
    message: str


def validate_repository(
    repo_root: Path,
    config_path: Path | None = None,
) -> list[ValidationIssue]:
    config = load_config(repo_root, config_path)
    try:
        artifacts = discover_artifacts(config)
    except ArtifactParseError as error:
        return [
            ValidationIssue(
                code=error.code,
                path=error.path.relative_to(config.repo_root),
                line=error.line,
                message=error.message,
            )
        ]
    issues: list[ValidationIssue] = []
    discovered_kinds = {artifact.kind for artifact in artifacts}
    required_artifacts = (
        (
            ArtifactKind.SPEC,
            config.spec_dir
            / config.spec_filename_template.format(feature=config.feature_slug),
        ),
        (
            ArtifactKind.ROADMAP,
            config.plan_dir
            / config.roadmap_filename_template.format(feature=config.feature_slug),
        ),
        (ArtifactKind.MILESTONE_PLAN, config.plan_dir),
    )
    for kind, expected_path in required_artifacts:
        if kind not in discovered_kinds:
            issues.append(
                ValidationIssue(
                    code="ARTIFACT_MISSING",
                    path=expected_path.relative_to(config.repo_root),
                    line=0,
                    message=f"required {kind.value} artifact is missing",
                )
            )
    if issues:
        return sorted(
            issues,
            key=lambda issue: (
                issue.path.as_posix().casefold(),
                issue.line,
                issue.code,
            ),
        )

    defined_requirements = {
        occurrence.value
        for artifact in artifacts
        if artifact.kind == ArtifactKind.SPEC
        for occurrence in artifact.occurrences
        if occurrence.category == "requirement"
        and occurrence.is_definition
        and occurrence.is_valid
    }
    requirement_locations: dict[str, tuple[Path, int]] = {}
    for artifact in artifacts:
        if artifact.kind != ArtifactKind.SPEC:
            continue
        for occurrence in artifact.occurrences:
            if (
                occurrence.category == "requirement"
                and occurrence.is_definition
                and occurrence.is_valid
            ):
                requirement_locations.setdefault(
                    occurrence.value,
                    (
                        artifact.path.relative_to(config.repo_root),
                        occurrence.line,
                    ),
                )
    roadmap_references = {
        requirement_id
        for artifact in artifacts
        if artifact.kind == ArtifactKind.ROADMAP
        for milestone in artifact.milestone_refs
        for requirement_id in milestone.requirement_ids
    }
    for requirement_id, (path, line) in requirement_locations.items():
        if requirement_id not in roadmap_references:
            issues.append(
                ValidationIssue(
                    code="REQ_REFERENCE_MISSING",
                    path=path,
                    line=line,
                    message=(
                        f"requirement is not referenced by roadmap: "
                        f"{requirement_id}"
                    ),
                )
            )
    roadmap_milestone_requirements: dict[str, set[str]] = {}
    for artifact in artifacts:
        if artifact.kind != ArtifactKind.ROADMAP:
            continue
        for milestone in artifact.milestone_refs:
            roadmap_milestone_requirements.setdefault(
                milestone.milestone_id,
                set(),
            ).update(milestone.requirement_ids)
    for artifact in artifacts:
        if artifact.kind != ArtifactKind.MILESTONE_PLAN:
            continue
        plan_requirement_references: set[str] = set()
        task_sections: list[dict[str, object]] = []
        current_task: dict[str, object] | None = None
        for occurrence in artifact.occurrences:
            if (
                current_task is not None
                and occurrence.line >= int(current_task["end_line"])
            ):
                current_task = None
            if (
                occurrence.category == "task"
                and occurrence.is_definition
                and occurrence.is_valid
            ):
                current_task = {
                    "id": occurrence.value,
                    "line": occurrence.line,
                    "end_line": occurrence.section_end_line,
                    "requirements": set(),
                }
                task_sections.append(current_task)
            elif (
                current_task is not None
                and occurrence.category == "requirement"
                and occurrence.is_valid
                and occurrence.value in defined_requirements
            ):
                requirements = current_task["requirements"]
                assert isinstance(requirements, set)
                requirements.add(occurrence.value)
                plan_requirement_references.add(occurrence.value)
        issue_path = artifact.path.relative_to(config.repo_root)
        for task in task_sections:
            requirements = task["requirements"]
            assert isinstance(requirements, set)
            if not requirements:
                issues.append(
                    ValidationIssue(
                        code="REQ_REFERENCE_MISSING",
                        path=issue_path,
                        line=int(task["line"]),
                        message=(
                            f"task has no known requirement reference: "
                            f"{task['id']}"
                        ),
                    )
                )
        assigned_requirements = roadmap_milestone_requirements.get(
            artifact.milestone_id or "",
            set(),
        )
        for requirement_id in sorted(assigned_requirements):
            if (
                requirement_id not in defined_requirements
                or requirement_id in plan_requirement_references
            ):
                continue
            path, line = requirement_locations[requirement_id]
            issues.append(
                ValidationIssue(
                    code="REQ_REFERENCE_MISSING",
                    path=path,
                    line=line,
                    message=(
                        f"requirement is not referenced by a milestone plan "
                        f"task: {requirement_id}"
                    ),
                )
            )
    seen_requirements: set[str] = set()
    seen_tasks: set[str] = set()
    for artifact in artifacts:
        for occurrence in artifact.occurrences:
            issue_path = artifact.path.relative_to(config.repo_root)
            if not occurrence.is_valid:
                code = (
                    "REQ_ID_INVALID"
                    if occurrence.category == "requirement"
                    else "TASK_ID_INVALID"
                )
                issues.append(
                    ValidationIssue(
                        code=code,
                        path=issue_path,
                        line=occurrence.line,
                        message=f"invalid {occurrence.category} ID: {occurrence.value}",
                    )
                )
                continue
            if occurrence.category == "task":
                if not occurrence.is_definition:
                    continue
                if occurrence.value in seen_tasks:
                    issues.append(
                        ValidationIssue(
                            code="TASK_ID_DUPLICATE",
                            path=issue_path,
                            line=occurrence.line,
                            message=f"duplicate task definition: {occurrence.value}",
                        )
                    )
                else:
                    seen_tasks.add(occurrence.value)
                continue
            is_spec_definition = (
                artifact.kind == ArtifactKind.SPEC
                and occurrence.is_definition
            )
            if is_spec_definition and occurrence.value in seen_requirements:
                issues.append(
                    ValidationIssue(
                        code="REQ_ID_DUPLICATE",
                        path=issue_path,
                        line=occurrence.line,
                        message=(
                            f"duplicate requirement definition: "
                            f"{occurrence.value}"
                        ),
                    )
                )
            elif is_spec_definition:
                seen_requirements.add(occurrence.value)
            elif occurrence.value not in defined_requirements:
                issues.append(
                    ValidationIssue(
                        code="REQ_REFERENCE_UNKNOWN",
                        path=issue_path,
                        line=occurrence.line,
                        message=(
                            f"unknown requirement reference: "
                            f"{occurrence.value}"
                        ),
                    )
                )
    return sorted(
        issues,
        key=lambda issue: (
            issue.path.as_posix().casefold(),
            issue.line,
            issue.code,
        ),
    )
