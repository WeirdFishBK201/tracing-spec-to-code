from __future__ import annotations

from pathlib import Path

from .artifacts import ArtifactKind, ArtifactParseError, discover_artifacts
from .config import load_config
from .issues import ValidationIssue, sort_issues


_KNOWN_STATUSES = {
    "Draft",
    "Awaiting",
    "Pending",
    "In Progress",
    "Approved",
    "Completed",
    "Delivered",
    "Rejected",
}
_COMPLETED_STATUSES = {"Completed", "Delivered"}

def _approval_status(artifact: object, name: str) -> tuple[str | None, int]:
    matches = [
        approval
        for approval in artifact.approval_refs
        if approval.name.casefold() == name.casefold()
    ]
    if len(matches) != 1:
        return None, artifact.status_line or 1
    return matches[0].status, matches[0].line


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
        return sort_issues(issues)

    for artifact in artifacts:
        if (
            artifact.status_count != 1
            or artifact.status not in _KNOWN_STATUSES
        ):
            issues.append(
                ValidationIssue(
                    code="WORKFLOW_STATUS_INVALID",
                    path=artifact.path.relative_to(config.repo_root),
                    line=artifact.status_line,
                    message="workflow status is missing or invalid",
                )
            )

    specs = [
        artifact
        for artifact in artifacts
        if artifact.kind == ArtifactKind.SPEC
    ]
    roadmaps = [
        artifact
        for artifact in artifacts
        if artifact.kind == ArtifactKind.ROADMAP
    ]
    plans = [
        artifact
        for artifact in artifacts
        if artifact.kind == ArtifactKind.MILESTONE_PLAN
    ]
    change_requests = [
        artifact
        for artifact in artifacts
        if artifact.kind == ArtifactKind.CHANGE_REQUEST
    ]
    roadmap = roadmaps[0]

    for artifact in artifacts:
        if (
            artifact.kind != ArtifactKind.ROADMAP
            and artifact.current_milestone_count
        ):
            issues.append(
                ValidationIssue(
                    code="CURRENT_MILESTONE_INVALID",
                    path=artifact.path.relative_to(config.repo_root),
                    line=artifact.current_milestone_line,
                    message=(
                        "current milestone metadata is only allowed on roadmap"
                    ),
                )
            )

    milestone_sequence: list[str] = []
    for milestone_ref in roadmap.milestone_refs:
        if milestone_ref.milestone_id not in milestone_sequence:
            milestone_sequence.append(milestone_ref.milestone_id)
    if (
        roadmap.current_milestone_count != 1
        or roadmap.current_milestone_id is None
        or roadmap.current_milestone_id not in milestone_sequence
    ):
        issues.append(
            ValidationIssue(
                code="CURRENT_MILESTONE_INVALID",
                path=roadmap.path.relative_to(config.repo_root),
                line=roadmap.current_milestone_line or 1,
                message="roadmap current milestone is missing or invalid",
            )
        )

    for artifact, approval_name, code in (
        (
            specs[0],
            "Requirements confirmation",
            "REQUIREMENTS_CONFIRMATION_MISSING",
        ),
        (roadmap, "Implementation approval", "IMPLEMENTATION_APPROVAL_MISSING"),
    ):
        approval_status, approval_line = _approval_status(
            artifact,
            approval_name,
        )
        if approval_status != "Approved":
            issues.append(
                ValidationIssue(
                    code=code,
                    path=artifact.path.relative_to(config.repo_root),
                    line=approval_line,
                    message=f"{approval_name} is not approved",
                )
            )

    active_plans = [
        plan
        for plan in plans
        if plan.status not in _COMPLETED_STATUSES
    ]
    if len(active_plans) > 1:
        for plan in active_plans[1:]:
            issues.append(
                ValidationIssue(
                    code="PLAN_MULTIPLE_ACTIVE",
                    path=plan.path.relative_to(config.repo_root),
                    line=plan.status_line,
                    message="more than one milestone plan is active",
                )
            )

    completed_plans = [
        plan for plan in plans if plan.status in _COMPLETED_STATUSES
    ]
    completed_plan_ids = {plan.milestone_id for plan in completed_plans}
    completed_milestones: set[str] = set()
    for milestone_id in milestone_sequence:
        if milestone_id not in completed_plan_ids:
            break
        completed_milestones.add(milestone_id)
    for plan in completed_plans:
        if plan.milestone_id not in completed_milestones:
            issues.append(
                ValidationIssue(
                    code="PLAN_NOT_NEXT_MILESTONE",
                    path=plan.path.relative_to(config.repo_root),
                    line=plan.status_line,
                    message=(
                        "completed plan is outside the contiguous roadmap "
                        "milestone prefix"
                    ),
                )
            )
    next_milestone = next(
        (
            milestone_id
            for milestone_id in milestone_sequence
            if milestone_id not in completed_milestones
        ),
        None,
    )
    if len(active_plans) == 1:
        active_plan = active_plans[0]
        if (
            active_plan.milestone_id != roadmap.current_milestone_id
            or active_plan.milestone_id != next_milestone
        ):
            issues.append(
                ValidationIssue(
                    code="PLAN_NOT_NEXT_MILESTONE",
                    path=active_plan.path.relative_to(config.repo_root),
                    line=active_plan.status_line,
                    message=(
                        "active plan does not match roadmap current and "
                        "next incomplete milestone"
                    ),
                )
            )
        approval_status, approval_line = _approval_status(
            active_plan,
            "Implementation approval",
        )
        if approval_status != "Approved":
            issues.append(
                ValidationIssue(
                    code="IMPLEMENTATION_APPROVAL_MISSING",
                    path=active_plan.path.relative_to(config.repo_root),
                    line=approval_line,
                    message="Implementation approval is not approved",
                )
            )
    elif (
        not active_plans
        and next_milestone is not None
        and not (
            roadmap.status == "Awaiting"
            and roadmap.current_milestone_id == next_milestone
        )
    ):
        issues.append(
            ValidationIssue(
                code="PLAN_NOT_NEXT_MILESTONE",
                path=roadmap.path.relative_to(config.repo_root),
                line=roadmap.status_line,
                message=f"no active plan for next milestone: {next_milestone}",
            )
        )

    for plan in plans:
        task_count = len(plan.task_ids)
        if task_count < 2 or task_count > 5:
            issues.append(
                ValidationIssue(
                    code="TASK_COUNT_INVALID",
                    path=plan.path.relative_to(config.repo_root),
                    line=plan.status_line or 1,
                    message=(
                        "milestone plan must define 2-5 valid tasks; "
                        f"found {task_count}"
                    ),
                )
            )

    for change_request in change_requests:
        approval_status, approval_line = _approval_status(
            change_request,
            "Change approval",
        )
        if (
            change_request.status != "Approved"
            or approval_status != "Approved"
        ):
            issues.append(
                ValidationIssue(
                    code="CHANGE_REQUEST_PENDING",
                    path=change_request.path.relative_to(config.repo_root),
                    line=approval_line,
                    message=(
                        "change request status and Change approval must be approved"
                    ),
                )
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
    return sort_issues(issues)
