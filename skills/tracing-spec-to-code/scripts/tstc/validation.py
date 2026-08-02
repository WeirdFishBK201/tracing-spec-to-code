from __future__ import annotations

from pathlib import Path

from .artifacts import ArtifactKind, ArtifactParseError, discover_artifacts
from .change_requests import change_request_id_from_filename
from .commit_message import validate_commit_message
from .config import load_config
from .evidence import (
    parse_evidence,
    validate_evidence,
    validate_evidence_schema,
    validate_traceability_references,
)
from .issues import ValidationIssue, sort_issues
from .lifecycle import CLOSED_PLAN_STATUSES, analyze_milestone_lifecycle


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

    def approved_change_data(plan: object) -> tuple[tuple[str, ...], tuple[str, ...]]:
        ids: list[str] = []
        checkpoint_artifacts: list[str] = []
        task_ids = set(getattr(plan, "task_ids", ()))
        for change_request in change_requests:
            metadata = change_request.change_request_metadata
            approval_status, _ = _approval_status(
                change_request,
                "Change approval",
            )
            if (
                change_request.status != "Approved"
                or approval_status != "Approved"
                or metadata is None
                or metadata.error is not None
                or not task_ids.intersection(metadata.affected_tasks)
            ):
                continue
            ids.append(
                change_request_id_from_filename(
                    config.change_request_filename_template,
                    config.feature_slug,
                    change_request.path.name,
                )
            )
            if (
                metadata.authoritative_spec_change is True
                and metadata.fact_change_commit_authorization == "Approved"
                and metadata.fact_change_base_commit is not None
            ):
                checkpoint_artifacts.extend(metadata.fact_change_artifacts)
        return tuple(dict.fromkeys(ids)), tuple(dict.fromkeys(checkpoint_artifacts))

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

    lifecycle = analyze_milestone_lifecycle(roadmap, plans)
    milestone_sequence = list(lifecycle.milestone_sequence)
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

    active_plans = list(lifecycle.active_plans)
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

    completed_plans = list(lifecycle.closed_plans)
    completed_milestones = set(lifecycle.closed_milestone_prefix)
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
    next_milestone = lifecycle.next_milestone_id
    if len(active_plans) == 1:
        active_plan = active_plans[0]
        if not lifecycle.active_plan_matches_current(roadmap):
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
        and not lifecycle.awaiting_current_is_valid(roadmap)
    ):
        if lifecycle.last_closed_plan_status == "Completed":
            guidance = (
                "; completed milestone awaiting delivery must remain current: "
                f"{lifecycle.last_closed_milestone_id}"
            )
        elif lifecycle.last_closed_plan_status == "Delivered":
            guidance = (
                "; delivered milestone handoff must set current milestone to: "
                f"{next_milestone}"
            )
        else:
            guidance = ""
        issues.append(
            ValidationIssue(
                code="PLAN_NOT_NEXT_MILESTONE",
                path=roadmap.path.relative_to(config.repo_root),
                line=roadmap.status_line,
                message=(
                    f"no active plan for next milestone: {next_milestone}"
                    f"{guidance}"
                ),
            )
        )
    if (
        not active_plans
        and next_milestone is None
        and lifecycle.closed_prefix_delivered
        and (
            roadmap.status != "Delivered"
            or roadmap.current_milestone_id
            != lifecycle.last_closed_milestone_id
        )
    ):
        issues.append(
            ValidationIssue(
                code="ROADMAP_TERMINAL_STATE_INVALID",
                path=roadmap.path.relative_to(config.repo_root),
                line=roadmap.status_line or 1,
                message=(
                    "final delivered milestone requires roadmap "
                    "Status: Delivered and Current milestone: "
                    f"{lifecycle.last_closed_milestone_id}"
                ),
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
        try:
            evidence = parse_evidence(config.repo_root, plan.path)
        except (OSError, UnicodeError) as error:
            issues.append(
                ValidationIssue(
                    code="ARTIFACT_PARSE_ERROR",
                    path=plan.path.relative_to(config.repo_root),
                    line=1,
                    message=f"cannot parse milestone evidence: {error}",
                )
            )
        else:
            _approved_ids, checkpoint_artifacts = approved_change_data(plan)
            if plan.status == "Completed":
                issues.extend(
                    validate_evidence(
                        evidence,
                        plan,
                        _approved_ids,
                    )
                )
            else:
                issues.extend(validate_evidence_schema(evidence))
            issues.extend(
                validate_traceability_references(
                    evidence,
                    plan_status=plan.status,
                    checkpoint_artifacts=checkpoint_artifacts,
                )
            )
            if (
                plan.status != "Delivered"
                and (evidence.commit_draft_count or evidence.commit_message)
            ):
                issues.extend(validate_commit_message(evidence))

    for change_request in change_requests:
        metadata = change_request.change_request_metadata
        if metadata is None or metadata.error is not None:
            issues.append(
                ValidationIssue(
                    code="CHANGE_REQUEST_METADATA_INVALID",
                    path=change_request.path.relative_to(config.repo_root),
                    line=metadata.line if metadata is not None else 1,
                    message=(
                        metadata.error
                        if metadata is not None and metadata.error is not None
                        else "Change Request metadata could not be parsed"
                    ),
                )
            )
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
