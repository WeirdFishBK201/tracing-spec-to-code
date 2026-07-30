from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from string import Formatter

from .config import ResolvedConfig


class ArtifactKind(str, Enum):
    SPEC = "spec"
    ROADMAP = "roadmap"
    MILESTONE_PLAN = "milestone_plan"
    CHANGE_PROPOSAL = "change_proposal"


@dataclass(frozen=True)
class IdOccurrence:
    value: str
    category: str
    line: int
    is_definition: bool
    is_valid: bool
    section_end_line: int | None = None


@dataclass(frozen=True)
class MilestoneRef:
    milestone_id: str
    line: int
    requirement_ids: tuple[str, ...]


@dataclass(frozen=True)
class GateRef:
    name: str
    status: str
    line: int


@dataclass(frozen=True)
class ArtifactRef:
    kind: ArtifactKind
    path: Path
    requirement_ids: tuple[str, ...]
    task_ids: tuple[str, ...]
    referenced_ids: tuple[str, ...]
    occurrences: tuple[IdOccurrence, ...] = ()
    milestone_id: str | None = None
    milestone_refs: tuple[MilestoneRef, ...] = ()
    status: str | None = None
    status_line: int = 0
    status_count: int = 0
    gate_refs: tuple[GateRef, ...] = ()
    current_milestone_id: str | None = None
    current_milestone_line: int = 0
    current_milestone_count: int = 0


class ArtifactParseError(Exception):
    def __init__(
        self,
        code: str,
        path: Path,
        line: int,
        message: str,
    ) -> None:
        self.code = code
        self.path = path
        self.line = line
        self.message = message
        super().__init__(message)


_REQUIREMENT_CANDIDATE = re.compile(r"\bREQ-[A-Za-z0-9-]+\b")
_REQUIREMENT_VALID = re.compile(
    r"REQ-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{3}\Z"
)
_TASK_CANDIDATE = re.compile(r"\bM\d+-T\d+\b")
_TASK_VALID = re.compile(r"M\d{2}-T\d{2}\Z")
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_MILESTONE_METADATA = re.compile(
    r"^-\s*Milestone\s*[:：]\s*(M\d{2})\b",
    re.IGNORECASE,
)
_MILESTONE_ID = re.compile(r"\bM(\d{2})\b", re.IGNORECASE)
_MILESTONE_RANGE = re.compile(
    r"\bM(\d{2})\s*[-–—]\s*M(\d{2})\b",
    re.IGNORECASE,
)
_METADATA_FIELD = re.compile(
    r"^-\s*(?P<label>Status|状态|Current milestone|当前 milestone|"
    r"Gate\s+(?P<gate>S|P|Δ))\s*[:：]\s*(?P<value>.*?)\s*$",
    re.IGNORECASE,
)
_CURRENT_MILESTONE_VALUE = re.compile(r"M\d{2}\Z", re.IGNORECASE)
_STATUS_PREFIXES = (
    "In Progress",
    "Completed",
    "Delivered",
    "Rejected",
    "Approved",
    "Awaiting",
    "Pending",
    "Draft",
)


def _normalized_status(value: str) -> str | None:
    folded = value.strip().casefold()
    for status in _STATUS_PREFIXES:
        prefix = status.casefold()
        if folded == prefix or (
            folded.startswith(prefix)
            and len(folded) > len(prefix)
            and not folded[len(prefix)].isalnum()
        ):
            return status
    return None


def _template_pattern(template: str, feature_slug: str) -> re.Pattern[str]:
    parts = []
    for literal, field_name, _, _ in Formatter().parse(template):
        parts.append(re.escape(literal))
        if field_name is None:
            continue
        if field_name == "feature":
            parts.append(re.escape(feature_slug))
        elif field_name in {"milestone", "proposal"}:
            parts.append(r"\d{2}")
        elif field_name in {"milestone_slug", "proposal_slug"}:
            parts.append(r"[A-Za-z0-9][A-Za-z0-9-]*")
    return re.compile(rf"\A{''.join(parts)}\Z")


def _has_section(headings: list[tuple[int, str]], expected: str) -> bool:
    expected_folded = expected.casefold()
    for level, text in headings:
        if level != 2:
            continue
        normalized = re.sub(r"^\d+(?:\.\d+)*\.?\s+", "", text).casefold()
        if normalized == expected_folded:
            return True
    return False


def _milestone_ids(value: str) -> tuple[str, ...]:
    found: list[str] = []
    for match in _MILESTONE_RANGE.finditer(value):
        start = int(match.group(1))
        end = int(match.group(2))
        if start <= end:
            found.extend(f"M{number:02d}" for number in range(start, end + 1))
    for match in _MILESTONE_ID.finditer(value):
        milestone_id = f"M{int(match.group(1)):02d}"
        if milestone_id not in found:
            found.append(milestone_id)
    return tuple(found)


def _parse_artifact(kind: ArtifactKind, path: Path) -> ArtifactRef:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise ArtifactParseError(
            "ARTIFACT_PARSE_ERROR",
            path,
            0,
            f"cannot read UTF-8 Markdown: {error}",
        ) from error

    headings: list[tuple[int, str]] = []
    heading_positions: list[tuple[int, int]] = []
    occurrences: list[tuple[int, int, IdOccurrence]] = []
    milestone_id: str | None = None
    milestone_refs: list[MilestoneRef] = []
    status: str | None = None
    status_line = 0
    status_count = 0
    gate_refs: list[GateRef] = []
    current_milestone_id: str | None = None
    current_milestone_line = 0
    current_milestone_count = 0
    in_top_metadata = True
    current_level_two_heading = ""
    for line_number, line in enumerate(lines, start=1):
        heading = _HEADING.match(line)
        heading_level = len(heading.group(1)) if heading else 0
        heading_text = heading.group(2) if heading else ""
        if heading_level >= 2:
            in_top_metadata = False
        if heading_level == 1:
            current_level_two_heading = ""
        elif heading_level == 2:
            current_level_two_heading = re.sub(
                r"^\d+(?:\.\d+)*\.?\s+",
                "",
                heading_text,
            ).casefold()
        if heading:
            headings.append((heading_level, heading_text))
            heading_positions.append((line_number, heading_level))

        candidates = [
            (match.start(), match.group(), "requirement", _REQUIREMENT_VALID)
            for match in _REQUIREMENT_CANDIDATE.finditer(line)
        ]
        candidates.extend(
            (match.start(), match.group(), "task", _TASK_VALID)
            for match in _TASK_CANDIDATE.finditer(line)
        )
        for column, value, category, valid_pattern in sorted(candidates):
            is_definition = (
                heading_level == 3
                and heading_text.startswith(value)
                and (
                    category != "task"
                    or current_level_two_heading == "tasks"
                )
                and (
                    len(heading_text) == len(value)
                    or not heading_text[len(value)].isalnum()
                )
            )
            occurrences.append(
                (
                    line_number,
                    column,
                    IdOccurrence(
                        value=value,
                        category=category,
                        line=line_number,
                        is_definition=is_definition,
                        is_valid=bool(valid_pattern.fullmatch(value)),
                    ),
                )
            )

        if in_top_metadata:
            metadata = _METADATA_FIELD.match(line)
            if metadata:
                label = metadata.group("label").casefold()
                value = metadata.group("value").strip()
                normalized = _normalized_status(value)
                if label in {"status", "状态"}:
                    status_count += 1
                    if status_count == 1:
                        status = normalized or value
                        status_line = line_number
                elif metadata.group("gate"):
                    gate_refs.append(
                        GateRef(
                            name=metadata.group("gate").upper(),
                            status=normalized or value,
                            line=line_number,
                        )
                    )
                else:
                    current_milestone_count += 1
                    current_milestone_line = line_number
                    current_milestone_id = None
                    if _CURRENT_MILESTONE_VALUE.fullmatch(value):
                        current_milestone_id = value.upper()

        if kind == ArtifactKind.MILESTONE_PLAN and milestone_id is None:
            metadata_match = _MILESTONE_METADATA.match(line)
            if metadata_match:
                milestone_id = metadata_match.group(1).upper()
        if kind == ArtifactKind.ROADMAP and line.lstrip().startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if cells:
                if (
                    len(cells) >= 2
                    and _REQUIREMENT_VALID.fullmatch(cells[0])
                ):
                    milestone_ids = _milestone_ids(cells[1])
                else:
                    milestone_ids = _milestone_ids(cells[0])
                if milestone_ids:
                    requirement_ids = tuple(
                        value
                        for _, value, category, valid_pattern in candidates
                        if category == "requirement"
                        and valid_pattern.fullmatch(value)
                    )
                    milestone_refs.extend(
                        MilestoneRef(
                            milestone_id=mapped_milestone,
                            line=line_number,
                            requirement_ids=requirement_ids,
                        )
                        for mapped_milestone in milestone_ids
                    )

    required_sections = {
        ArtifactKind.SPEC: ("Requirements",),
        ArtifactKind.ROADMAP: ("Milestones",),
        ArtifactKind.MILESTONE_PLAN: ("Tasks",),
        ArtifactKind.CHANGE_PROPOSAL: ("Proposed delta", "Impact"),
    }
    missing = [
        section
        for section in required_sections[kind]
        if not _has_section(headings, section)
    ]
    if missing:
        raise ArtifactParseError(
            "ARTIFACT_PARSE_ERROR",
            path,
            1,
            f"missing required section: {missing[0]}",
        )
    if kind == ArtifactKind.MILESTONE_PLAN and milestone_id is None:
        raise ArtifactParseError(
            "ARTIFACT_PARSE_ERROR",
            path,
            1,
            "missing milestone metadata",
        )

    ordered_items: list[IdOccurrence] = []
    for _, _, occurrence in sorted(occurrences):
        if occurrence.category == "task" and occurrence.is_definition:
            section_end_line = next(
                (
                    heading_line
                    for heading_line, heading_level in heading_positions
                    if heading_line > occurrence.line and heading_level <= 3
                ),
                len(lines) + 1,
            )
            occurrence = IdOccurrence(
                value=occurrence.value,
                category=occurrence.category,
                line=occurrence.line,
                is_definition=occurrence.is_definition,
                is_valid=occurrence.is_valid,
                section_end_line=section_end_line,
            )
        ordered_items.append(occurrence)
    ordered_occurrences = tuple(ordered_items)
    requirement_ids = tuple(
        item.value
        for item in ordered_occurrences
        if item.category == "requirement"
        and kind == ArtifactKind.SPEC
        and item.is_definition
        and item.is_valid
    )
    task_ids = tuple(
        item.value
        for item in ordered_occurrences
        if item.category == "task" and item.is_definition and item.is_valid
    )
    referenced_ids = tuple(
        item.value
        for item in ordered_occurrences
        if item.is_valid
        and (
            not item.is_definition
            or (
                item.category == "requirement"
                and kind != ArtifactKind.SPEC
            )
        )
    )
    return ArtifactRef(
        kind=kind,
        path=path,
        requirement_ids=requirement_ids,
        task_ids=task_ids,
        referenced_ids=referenced_ids,
        occurrences=ordered_occurrences,
        milestone_id=milestone_id,
        milestone_refs=tuple(milestone_refs),
        status=status,
        status_line=status_line,
        status_count=status_count,
        gate_refs=tuple(gate_refs),
        current_milestone_id=current_milestone_id,
        current_milestone_line=current_milestone_line,
        current_milestone_count=current_milestone_count,
    )


def discover_artifacts(config: ResolvedConfig) -> list[ArtifactRef]:
    candidates: list[tuple[ArtifactKind, Path]] = []
    spec_path = config.spec_dir / config.spec_filename_template.format(
        feature=config.feature_slug
    )
    if spec_path.is_file():
        candidates.append((ArtifactKind.SPEC, spec_path))

    roadmap_path = config.plan_dir / config.roadmap_filename_template.format(
        feature=config.feature_slug
    )
    if roadmap_path.is_file():
        candidates.append((ArtifactKind.ROADMAP, roadmap_path))

    plan_pattern = _template_pattern(
        config.milestone_plan_filename_template,
        config.feature_slug,
    )
    if config.plan_dir.is_dir():
        candidates.extend(
            (ArtifactKind.MILESTONE_PLAN, path)
            for path in sorted(config.plan_dir.iterdir())
            if path.is_file() and plan_pattern.fullmatch(path.name)
        )

    proposal_pattern = _template_pattern(
        config.change_proposal_filename_template,
        config.feature_slug,
    )
    if config.change_dir.is_dir():
        candidates.extend(
            (ArtifactKind.CHANGE_PROPOSAL, path)
            for path in sorted(config.change_dir.iterdir())
            if path.is_file() and proposal_pattern.fullmatch(path.name)
        )

    return [_parse_artifact(kind, path) for kind, path in candidates]
