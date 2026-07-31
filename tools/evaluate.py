from __future__ import annotations

import argparse
import hashlib
import json
import re
import secrets
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

if __package__:
    from .distribution import DistributionError, load_registry
else:
    from distribution import DistributionError, load_registry  # type: ignore[no-redef]


_RUN_TYPES = {"baseline", "pressure", "wording", "level1", "level2"}
_OUTCOMES = {"observed", "pass", "fail", "blocked"}
_PRESSURE_KINDS = {
    "time",
    "authority",
    "sunk-cost",
    "exceptionalism",
    "silence",
    "scope-expansion",
}
_EVIDENCE_V1_KEYS = {
    "schema_version",
    "run_id",
    "case_id",
    "client_id",
    "skill_loaded",
    "client_version",
    "model",
    "config",
    "recorded_at",
    "prompt",
    "actual_decision",
    "verbatim_rationale",
    "outcome",
    "reason",
    "notes",
    "rationale_review",
    "supersedes_run_ids",
}
_EVIDENCE_V2_KEYS = _EVIDENCE_V1_KEYS | {
    "runtime_surface",
    "attempt_id",
    "prepared_at",
    "session_ref",
    "rerun_of",
    "change_proposal",
}
_REFERENCE_RUN_TYPES = {"baseline", "pressure", "wording"}
_REFERENCE_CLIENT = "codex"
_CP09_RERUN_MAPPING = {
    "baseline-gate-02": ("gate-baseline", "baseline-gate-01"),
    "baseline-context-02": ("context-baseline", "baseline-context-01"),
    "baseline-verification-git-02": (
        "verification-git-baseline",
        "baseline-verification-git-01",
    ),
    "loaded-gate-02": ("gate-loaded", "loaded-gate-01"),
    "loaded-context-02": ("context-loaded", "loaded-context-01"),
    "loaded-verification-git-02": (
        "verification-git-loaded",
        "loaded-verification-git-01",
    ),
    **{
        f"wording-semantic-scope-{new:02d}": (
            "wording-semantic-scope",
            f"wording-semantic-scope-{old:02d}",
        )
        for new, old in zip(range(6, 11), range(1, 6), strict=True)
    },
    **{
        f"wording-commit-boundary-{new:02d}": (
            "wording-commit-boundary",
            f"wording-commit-boundary-{old:02d}",
        )
        for new, old in zip(range(6, 11), range(1, 6), strict=True)
    },
}
_CP09_CASE_IDS = {case_id for case_id, _ in _CP09_RERUN_MAPPING.values()}
_CP10_RERUN_MAPPING = {
    f"wording-commit-boundary-{new:02d}": (
        "wording-commit-boundary",
        f"wording-commit-boundary-{old:02d}",
    )
    for new, old in zip(range(11, 16), range(6, 11), strict=True)
}
_CP10_SOURCE_DIGESTS = {
    "baseline-context-02": "523351389dd59f445371a1c98e207f54e543eec8324b9250c4cee146394db007",
    "baseline-gate-02": "c549741f43fb996a39a746f5ca00ce478e6e693bd0271f31a785873f20c7c3c5",
    "baseline-verification-git-02": "686aa89ceb5cdf38934cc3531bcfe5095037c3e5b2cc0231722c362e4945e121",
    "loaded-context-02": "f10f76bbdbaa2e79f2c6ea9081bc98777257caa5b3c221726625b594393633e5",
    "loaded-gate-02": "9f8b26de748cb51f071de8bf2000fd46df781929efa950f812f4d0ac84910c1d",
    "loaded-verification-git-02": "d42b1792eb215ab5ff2a85579efa74c9839861e073b50abd8a3d3528350760ed",
    "wording-commit-boundary-06": "9568ab615b0a69fd6191dda2fd7410735b7cbf60299f9abf5aba439df68e05f6",
    "wording-commit-boundary-07": "436d2c70eeb8f5ed4096769f80dfebacabc4f1afd2f3166896747ba3db683671",
    "wording-commit-boundary-08": "c8b3942d441f4a47ef14b26252820541a9605191785a6718a402a6da0db62bbf",
    "wording-commit-boundary-09": "5b237306f0c763942c31feef6ff5a484f1b23c1aa5219f78decb0ba5974cb443",
    "wording-commit-boundary-10": "3241dfd0c67db0551e11ea3d57b4fb120b57fa6553c92aa839823ea07cc182a1",
    "wording-semantic-scope-06": "0dc6ccb380225c5730378fdd2dc8f2880c9adf2dfdba3872ba62f9b12bf79e6a",
    "wording-semantic-scope-07": "eb30ab1bbf513c1eb85c9993d126a9e85030575a79a7fdb561f7778016bb169e",
    "wording-semantic-scope-08": "e888336c29f43b4c34c41fc640e1f131565bd3938231b0dc0648a09e9e37de21",
    "wording-semantic-scope-09": "5de5943b15d506911194b712eef63f1b868ffff173235a77956ef6ef381e0896",
    "wording-semantic-scope-10": "4fa227f975591ad987afb3d960b4619eba5cf37c5468a99cd14ef80ce0f1523b",
}
_PLACEHOLDER_ENVIRONMENT_VALUES = {
    "n/a",
    "na",
    "not available",
    "not specified",
    "precise version unavailable",
    "unknown",
    "unavailable",
    "unspecified",
}


class EvaluationError(Exception):
    def __init__(self, code: str, message: str, path: Path | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.path = path


@dataclass(frozen=True)
class CaseSpec:
    id: str
    scenario_id: str
    run_type: str
    prompt: str
    skill_loaded: bool
    expected_decision: str
    pressures: tuple[tuple[str, str], ...] = ()
    variant_group: str | None = None
    decision_options: tuple[str, ...] = ()
    response_contract: str | None = None
    document_schema_version: int = 1


@dataclass(frozen=True)
class EvidenceRecord:
    schema_version: int
    run_id: str
    case_id: str
    client_id: str
    skill_loaded: bool
    client_version: str
    model: str
    config: dict[str, Any]
    runtime_surface: str | None
    attempt_id: str | None
    prepared_at: str | None
    session_ref: str | None
    recorded_at: str
    prompt: str
    actual_decision: str
    verbatim_rationale: str
    outcome: str
    reason: str
    notes: tuple[str, ...]
    rationale_review: dict[str, Any]
    supersedes_run_ids: tuple[str, ...]
    rerun_of: str | None
    change_proposal: str | None


@dataclass(frozen=True)
class EvaluationSummary:
    baseline_observed: int
    pressure_passed: int
    wording_groups: dict[str, int]
    level1_passed: int
    level2_passed: int
    blocked_runs: int
    failed_runs: int
    open_rationales: int


def _case_error(message: str, path: Path) -> EvaluationError:
    return EvaluationError("CASE_INVALID", message, path)


def load_cases(path: Path) -> tuple[CaseSpec, ...]:
    try:
        payload = _load_json(path, "CASE_INVALID")
    except EvaluationError as error:
        raise _case_error(str(error), path) from error
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "cases"}:
        raise _case_error("case document must contain only schema_version and cases", path)
    if payload["schema_version"] not in {1, 2} or not isinstance(payload["cases"], list):
        raise _case_error("case document schema is invalid", path)

    cases: list[CaseSpec] = []
    seen_ids: set[str] = set()
    for raw in payload["cases"]:
        if not isinstance(raw, dict):
            raise _case_error("case must be an object", path)
        required = {
            "id",
            "scenario_id",
            "run_type",
            "prompt",
            "skill_loaded",
            "expected_decision",
        }
        optional = {
            "pressures",
            "variant_group",
            "decision_options",
            "response_contract",
        }
        if not required.issubset(raw) or set(raw) - (required | optional):
            raise _case_error("case keys are invalid", path)
        case_id = raw["id"]
        scenario_id = raw["scenario_id"]
        run_type = raw["run_type"]
        prompt = raw["prompt"]
        expected_decision = raw["expected_decision"]
        if (
            not all(isinstance(value, str) and value for value in (case_id, scenario_id, prompt, expected_decision))
            or not isinstance(raw["skill_loaded"], bool)
            or not isinstance(run_type, str)
            or run_type not in _RUN_TYPES
            or case_id in seen_ids
        ):
            raise _case_error("case values are invalid", path)
        seen_ids.add(case_id)

        pressures: tuple[tuple[str, str], ...] = ()
        if run_type in {"pressure", "wording"}:
            raw_pressures = raw.get("pressures")
            if not isinstance(raw_pressures, list) or len(raw_pressures) < 3:
                message = (
                    "wording case needs a behavioral contract with three pressures"
                    if run_type == "wording"
                    else "pressure case needs three pressures"
                )
                raise _case_error(message, path)
            parsed_pressures: list[tuple[str, str]] = []
            for pressure in raw_pressures:
                if not isinstance(pressure, dict) or set(pressure) != {"kind", "excerpt"}:
                    raise _case_error("pressure must contain kind and excerpt", path)
                kind = pressure["kind"]
                excerpt = pressure["excerpt"]
                if (
                    not isinstance(kind, str)
                    or kind not in _PRESSURE_KINDS
                    or not isinstance(excerpt, str)
                    or not excerpt
                    or excerpt not in prompt
                ):
                    raise _case_error("pressure is invalid", path)
                parsed_pressures.append((kind, excerpt))
            if len({kind for kind, _ in parsed_pressures}) != len(parsed_pressures):
                raise _case_error("pressure kinds must be distinct", path)
            pressures = tuple(parsed_pressures)
        elif "pressures" in raw:
            raise _case_error("only pressure and wording cases may contain pressures", path)

        variant_group = raw.get("variant_group")
        decision_options: tuple[str, ...] = ()
        response_contract = raw.get("response_contract")
        if run_type == "wording":
            raw_options = raw.get("decision_options")
            if (
                not isinstance(variant_group, str)
                or not variant_group
                or not isinstance(raw_options, list)
                or len(raw_options) < 2
                or not all(isinstance(option, str) and option for option in raw_options)
                or len(set(raw_options)) != len(raw_options)
                or expected_decision not in raw_options
                or not all(option in prompt for option in raw_options)
                or not isinstance(response_contract, str)
                or not response_contract
                or response_contract not in prompt
            ):
                raise _case_error("wording case needs a behavioral decision contract", path)
            decision_options = tuple(raw_options)
        elif (
            variant_group is not None
            or "variant_group" in raw
            or "decision_options" in raw
            or "response_contract" in raw
        ):
            raise _case_error("only wording cases may contain wording contract fields", path)
        if (
            (run_type == "baseline" and (raw["skill_loaded"] or expected_decision != "observed"))
            or (run_type != "baseline" and not raw["skill_loaded"])
        ):
            raise _case_error("run type conflicts with skill_loaded or expected_decision", path)

        cases.append(
            CaseSpec(
                id=case_id,
                scenario_id=scenario_id,
                run_type=run_type,
                prompt=prompt,
                skill_loaded=raw["skill_loaded"],
                expected_decision=expected_decision,
                pressures=pressures,
                variant_group=variant_group,
                decision_options=decision_options,
                response_contract=response_contract,
                document_schema_version=payload["schema_version"],
            )
        )
    pairings: dict[str, list[CaseSpec]] = {}
    for case in cases:
        if case.run_type in {"baseline", "pressure"}:
            pairings.setdefault(case.scenario_id, []).append(case)
    for scenario_cases in pairings.values():
        if len(scenario_cases) != 2 or {case.run_type for case in scenario_cases} != {
            "baseline",
            "pressure",
        }:
            raise _case_error("baseline and pressure cases must form one pair", path)
    return tuple(cases)


def _evidence_error(code: str, message: str, path: Path) -> EvaluationError:
    return EvaluationError(code, message, path)


def _is_repository_path(path: Path) -> bool:
    try:
        path.resolve().relative_to(Path(__file__).resolve().parents[1])
    except (OSError, ValueError):
        return False
    return True


def _load_json(path: Path, code: str) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate JSON key: {key}")
            value[key] = item
        return value

    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    except (OSError, ValueError) as error:
        raise _evidence_error(code, f"cannot load JSON: {error}", path) from error
    if not isinstance(value, dict):
        raise _evidence_error(code, "JSON document must be an object", path)
    return value


def _contains_sensitive_content(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            key.casefold() in {"secret", "password", "token"} and item not in (None, "", [], {})
            or _contains_sensitive_content(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_sensitive_content(item) for item in value)
    if not isinstance(value, str):
        return False
    normalized = value.casefold().replace("/", "\\")
    home_path = str(Path.home()).casefold().replace("/", "\\")
    repository_root = str(Path(__file__).resolve().parents[1]).casefold().replace("/", "\\").rstrip("\\")
    absolute_paths = re.findall(r"(?<![A-Za-z0-9_])(?:[A-Za-z]:[\\/]|\\\\|\\|/)[^\s\"'`<>]*", value)
    has_external_path = any(
        not (candidate.casefold().replace("/", "\\") == repository_root or candidate.casefold().replace("/", "\\").startswith(repository_root + "\\"))
        for candidate in absolute_paths
    )
    return (
        bool(re.search(r"\b(?:sk|api)[-_][A-Za-z0-9_-]{16,}\b", value))
        or "vgccoach2" in normalized
        or "agentic-workflow" in normalized
        or home_path in normalized
        or has_external_path
    )


def _parse_utc_timestamp(value: str, field: str, path: Path) -> datetime:
    try:
        if not value.endswith("Z"):
            raise ValueError("UTC timestamp must end with Z")
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise _evidence_error(
            "EVIDENCE_INVALID",
            f"{field} must be a UTC timestamp",
            path,
        ) from error


def _is_placeholder_environment(value: str) -> bool:
    normalized = re.sub(r"\s+", " ", value.strip().casefold())
    return normalized in _PLACEHOLDER_ENVIRONMENT_VALUES or "unavailable" in normalized


def _parse_evidence(raw: dict[str, Any], path: Path) -> EvidenceRecord:
    schema_version = raw.get("schema_version")
    expected_keys = (
        _EVIDENCE_V1_KEYS
        if schema_version == 1
        else _EVIDENCE_V2_KEYS
        if schema_version == 2
        else None
    )
    if expected_keys is None or set(raw) != expected_keys:
        raise _evidence_error("EVIDENCE_INVALID", "evidence keys are invalid", path)
    if _contains_sensitive_content(raw):
        raise _evidence_error("SENSITIVE_CONTENT", "evidence contains sensitive content", path)
    required_strings = (
        "run_id", "case_id", "client_id", "client_version", "model", "recorded_at",
        "prompt", "actual_decision", "verbatim_rationale", "outcome", "reason",
    )
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or not all(isinstance(raw[field], str) and raw[field] for field in required_strings if field != "reason")
        or not isinstance(raw["reason"], str)
        or raw["outcome"] not in _OUTCOMES
        or not isinstance(raw["run_id"], str)
        or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,79}", raw["run_id"])
        or not isinstance(raw["skill_loaded"], bool)
        or not isinstance(raw["config"], dict)
        or not isinstance(raw["notes"], list)
        or not all(isinstance(note, str) and note for note in raw["notes"])
        or not isinstance(raw["rationale_review"], dict)
        or not isinstance(raw["supersedes_run_ids"], list)
        or not all(isinstance(run_id, str) and re.fullmatch(r"[a-z0-9][a-z0-9-]{2,79}", run_id) for run_id in raw["supersedes_run_ids"])
        or len(set(raw["supersedes_run_ids"])) != len(raw["supersedes_run_ids"])
    ):
        raise _evidence_error("EVIDENCE_INVALID", "evidence values are invalid", path)
    if raw["outcome"] in {"fail", "blocked"} and not raw["reason"]:
        raise _evidence_error("EVIDENCE_INVALID", "failed or blocked evidence needs a reason", path)
    if raw["outcome"] not in {"fail", "blocked"} and raw["reason"]:
        raise _evidence_error("EVIDENCE_INVALID", "successful evidence cannot contain a failure reason", path)

    runtime_surface: str | None = None
    attempt_id: str | None = None
    prepared_at: str | None = None
    session_ref: str | None = None
    rerun_of: str | None = None
    change_proposal: str | None = None
    if schema_version == 2:
        runtime_surface = raw["runtime_surface"]
        attempt_id = raw["attempt_id"]
        prepared_at = raw["prepared_at"]
        session_ref = raw["session_ref"]
        rerun_of = raw["rerun_of"]
        change_proposal = raw["change_proposal"]
        identity_pattern = r"[A-Za-z0-9][A-Za-z0-9._-]{2,127}"
        if (
            not all(
                isinstance(value, str) and value
                for value in (runtime_surface, attempt_id, prepared_at, session_ref)
            )
            or not re.fullmatch(identity_pattern, attempt_id)
            or not re.fullmatch(identity_pattern, session_ref)
            or not isinstance(rerun_of, (str, type(None)))
            or (
                isinstance(rerun_of, str)
                and not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,79}", rerun_of)
            )
            or not isinstance(change_proposal, (str, type(None)))
            or (
                isinstance(change_proposal, str)
                and not re.fullmatch(r"CP-\d+", change_proposal, flags=re.IGNORECASE)
            )
            or (rerun_of is None) != (change_proposal is None)
        ):
            raise _evidence_error("EVIDENCE_INVALID", "schema-v2 execution metadata is invalid", path)
        if any(
            _is_placeholder_environment(value)
            for value in (raw["client_version"], raw["model"], runtime_surface)
        ):
            raise _evidence_error(
                "EVIDENCE_INVALID",
                "exact environment metadata cannot use placeholder values",
                path,
            )
        prepared_time = _parse_utc_timestamp(prepared_at, "prepared_at", path)
        recorded_time = _parse_utc_timestamp(raw["recorded_at"], "recorded_at", path)
        if recorded_time <= prepared_time:
            raise _evidence_error(
                "EVIDENCE_INVALID",
                "recorded_at must be after prepared_at",
                path,
            )

    review = raw["rationale_review"]
    if set(review) != {"status", "reviewer", "rule_refs", "change_proposal_id"}:
        raise _evidence_error("EVIDENCE_INVALID", "rationale review keys are invalid", path)
    if (
        review["status"] not in {"no-new-rationale", "covered", "new-rationale"}
        or not isinstance(review["reviewer"], str)
        or not review["reviewer"]
        or not isinstance(review["rule_refs"], list)
        or not all(isinstance(rule_ref, str) and rule_ref for rule_ref in review["rule_refs"])
        or (review["change_proposal_id"] is not None and (not isinstance(review["change_proposal_id"], str) or not review["change_proposal_id"]))
        or (review["status"] == "new-rationale" and raw["outcome"] == "pass")
    ):
        raise _evidence_error("EVIDENCE_INVALID", "rationale review is invalid", path)
    _parse_utc_timestamp(raw["recorded_at"], "recorded_at", path)
    return EvidenceRecord(
        schema_version=schema_version, run_id=raw["run_id"], case_id=raw["case_id"],
        client_id=raw["client_id"], skill_loaded=raw["skill_loaded"],
        client_version=raw["client_version"], model=raw["model"], config=raw["config"],
        runtime_surface=runtime_surface, attempt_id=attempt_id,
        prepared_at=prepared_at, session_ref=session_ref,
        recorded_at=raw["recorded_at"], prompt=raw["prompt"],
        actual_decision=raw["actual_decision"], verbatim_rationale=raw["verbatim_rationale"],
        outcome=raw["outcome"], reason=raw["reason"], notes=tuple(raw["notes"]),
        rationale_review=review, supersedes_run_ids=tuple(raw["supersedes_run_ids"]),
        rerun_of=rerun_of, change_proposal=change_proposal,
    )


def _validate_record_contract(
    record: EvidenceRecord,
    case: CaseSpec,
    clients: set[str],
    path: Path,
) -> None:
    if (
        case.document_schema_version == 2
        and case.run_type in _REFERENCE_RUN_TYPES
        and record.schema_version != 2
    ):
        raise _evidence_error(
            "EVIDENCE_INVALID",
            "active reference evidence requires schema v2",
            path,
        )
    if record.change_proposal == "CP-10" or (
        case.document_schema_version == 2 and case.id in _CP09_CASE_IDS
    ):
        mapping = (
            _CP10_RERUN_MAPPING
            if record.change_proposal == "CP-10"
            else _CP09_RERUN_MAPPING
        )
        expected = mapping.get(record.run_id)
        expected_supersessions = (
            (record.rerun_of,)
            if record.change_proposal == "CP-10"
            else ()
        )
        expected_proposal = (
            "CP-10" if record.change_proposal == "CP-10" else "CP-09"
        )
        if (
            expected != (case.id, record.rerun_of)
            or record.change_proposal != expected_proposal
            or record.supersedes_run_ids != expected_supersessions
        ):
            raise _evidence_error(
                "EVIDENCE_INVALID",
                "canonical reference evidence requires an exact approved rerun mapping",
                path,
            )
    if record.client_id not in clients:
        raise _evidence_error("EVIDENCE_INVALID", "client_id is unknown", path)
    if record.skill_loaded is not case.skill_loaded or record.prompt != case.prompt:
        raise _evidence_error("EVIDENCE_INVALID", "evidence does not match its case", path)
    if case.run_type in _REFERENCE_RUN_TYPES and record.client_id != _REFERENCE_CLIENT:
        raise _evidence_error("EVIDENCE_INVALID", "reference cases must use Codex", path)
    if case.run_type == "baseline":
        if record.outcome not in {"observed", "blocked"}:
            raise _evidence_error("EVIDENCE_INVALID", "baseline outcome is invalid", path)
    elif record.outcome == "observed":
        raise _evidence_error("EVIDENCE_INVALID", "only baselines may be observed", path)
    elif record.outcome == "pass" and record.actual_decision != case.expected_decision:
        raise _evidence_error("EVIDENCE_INVALID", "passing decision does not match its case", path)


def record_evidence(
    input_path: Path,
    evidence_dir: Path,
    cases_path: Path,
    registry_path: Path,
) -> Path:
    raw = _load_json(input_path, "EVIDENCE_INVALID")
    record = _parse_evidence(raw, input_path)
    cases = {case.id: case for case in load_cases(cases_path)}
    case = cases.get(record.case_id)
    if case is None:
        raise _evidence_error("EVIDENCE_INVALID", "case_id is unknown", input_path)
    try:
        clients = {client.id for client in load_registry(registry_path)}
    except DistributionError as error:
        raise _evidence_error("EVIDENCE_INVALID", str(error), registry_path) from error
    _validate_record_contract(record, case, clients, input_path)

    target = evidence_dir / f"{record.run_id}.json"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(raw, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError as error:
        raise _evidence_error("RUN_EXISTS", "run_id already exists", target) from error
    return target


def load_evidence(path: Path) -> EvidenceRecord:
    raw = _load_json(path, "EVIDENCE_INVALID")
    return _parse_evidence(raw, path)


def validate_suite(
    cases_path: Path,
    registry_path: Path,
    evidence_dir: Path,
    run_types: set[str] | None = None,
) -> EvaluationSummary:
    cases = load_cases(cases_path)
    try:
        clients = {client.id: client for client in load_registry(registry_path)}
    except DistributionError as error:
        raise _evidence_error("EVIDENCE_INVALID", str(error), registry_path) from error
    paths = tuple(sorted(evidence_dir.glob("*.json"))) if evidence_dir.is_dir() else ()
    if not paths:
        raise _evidence_error(
            "EVALUATION_INCOMPLETE",
            "evidence directory has no recorded runs",
            evidence_dir,
        )
    records = tuple(load_evidence(path) for path in paths)
    case_map = {case.id: case for case in cases}
    if len({record.run_id for record in records}) != len(records):
        raise _evidence_error("EVIDENCE_INVALID", "run_id is duplicated", evidence_dir)
    by_case: dict[str, list[EvidenceRecord]] = {}
    for record in records:
        case = case_map.get(record.case_id)
        if case is None:
            raise _evidence_error("EVIDENCE_INVALID", "evidence references an unknown case", evidence_dir)
        _validate_record_contract(record, case, set(clients), evidence_dir)
        by_case.setdefault(record.case_id, []).append(record)

    selected_cases = tuple(case for case in cases if run_types is None or case.run_type in run_types)
    selected_ids = {case.id for case in selected_cases}
    selected_records = tuple(record for record in records if record.case_id in selected_ids)
    record_map = {record.run_id: record for record in records}
    approved_proposals = _approved_change_proposals(registry_path)

    v2_records = tuple(record for record in records if record.schema_version == 2)
    attempt_ids = [record.attempt_id for record in v2_records]
    session_refs = [record.session_ref for record in v2_records]
    if len(set(attempt_ids)) != len(attempt_ids) or len(set(session_refs)) != len(session_refs):
        raise _evidence_error(
            "EVALUATION_FAILED",
            "schema-v2 runs must have distinct execution identity",
            evidence_dir,
        )

    cp09_reruns = tuple(
        record for record in records if record.change_proposal == "CP-09"
    )
    if cp09_reruns:
        rerun_sources = [record.rerun_of for record in cp09_reruns]
        if len(set(rerun_sources)) != len(rerun_sources):
            raise _evidence_error(
                "EVALUATION_FAILED",
                "archived rerun source is referenced more than once",
                evidence_dir,
            )
        archive_dir = evidence_dir.parent / "archive" / "cp09"
        archive_paths = (
            tuple(sorted(archive_dir.glob("*.json")))
            if archive_dir.is_dir()
            else ()
        )
        archive_records = tuple(load_evidence(path) for path in archive_paths)
        archive_map = {record.run_id: record for record in archive_records}
        if (
            len(archive_map) != len(archive_records)
            or set(archive_map) != set(rerun_sources)
        ):
            raise _evidence_error(
                "EVALUATION_INCOMPLETE",
                "archived rerun source set is incomplete",
                archive_dir,
            )
        for record in cp09_reruns:
            source = archive_map[record.rerun_of or ""]
            if (
                record.schema_version != 2
                or source.schema_version != 1
                or record.change_proposal != "CP-09"
                or "CP-09" not in approved_proposals
                or source.case_id != record.case_id
                or _timestamp(record.recorded_at) <= _timestamp(source.recorded_at)
            ):
                raise _evidence_error(
                    "EVALUATION_FAILED",
                    "archived rerun source mapping is invalid",
                    evidence_dir,
                )

    cp10_reruns = tuple(
        record for record in records if record.change_proposal == "CP-10"
    )
    cp10_source_ids: set[str] = set()
    if cp10_reruns:
        evidence_paths = {path.stem: path for path in paths}
        if any(
            source_id not in evidence_paths
            or _semantic_json_digest(evidence_paths[source_id]) != expected_digest
            for source_id, expected_digest in _CP10_SOURCE_DIGESTS.items()
        ):
            raise _evidence_error(
                "EVALUATION_FAILED",
                "CP-10 source integrity check failed",
                evidence_dir,
            )
        expected_cp10_ids = set(_CP10_RERUN_MAPPING)
        if (
            {record.run_id for record in cp10_reruns} != expected_cp10_ids
            or "CP-10" not in approved_proposals
        ):
            raise _evidence_error(
                "EVALUATION_FAILED",
                "CP-10 wording rebuild must contain the exact approved five-run mapping",
                evidence_dir,
            )
        fingerprints = set()
        for record in cp10_reruns:
            expected_case, expected_source = _CP10_RERUN_MAPPING[record.run_id]
            source = record_map.get(expected_source)
            if (
                source is None
                or record.case_id != expected_case
                or record.rerun_of != expected_source
                or record.supersedes_run_ids != (expected_source,)
                or record.outcome != "pass"
                or record.actual_decision != case_map[record.case_id].expected_decision
                or _timestamp(record.recorded_at) <= _timestamp(source.recorded_at)
            ):
                raise _evidence_error(
                    "EVALUATION_FAILED",
                    "CP-10 wording rebuild mapping is invalid",
                    evidence_dir,
                )
            if _timestamp(record.prepared_at or "") <= _timestamp(
                source.recorded_at
            ):
                raise _evidence_error(
                    "EVALUATION_FAILED",
                    "CP-10 replacement must be prepared after its source",
                    evidence_dir,
                )
            cp10_source_ids.add(expected_source)
            fingerprints.add(
                (
                    record.schema_version,
                    record.client_id,
                    record.client_version,
                    record.model,
                    json.dumps(record.config, sort_keys=True),
                    record.runtime_surface,
                )
            )
        trigger_id = "wording-commit-boundary-07"
        trigger = record_map.get(trigger_id)
        identity_sets = (
            {record.attempt_id for record in cp10_reruns},
            {record.session_ref for record in cp10_reruns},
            {record.recorded_at for record in cp10_reruns},
        )
        if (
            len(fingerprints) != 1
            or trigger is None
            or trigger.rationale_review["status"] != "new-rationale"
            or trigger.outcome != "fail"
            or any(
                record_map[source_id].rationale_review["status"] == "new-rationale"
                for source_id in cp10_source_ids - {trigger_id}
            )
        ):
            raise _evidence_error(
                "EVALUATION_FAILED",
                "CP-10 wording rebuild environment or rationale source is invalid",
                evidence_dir,
            )
        if any(len(values) != len(cp10_reruns) for values in identity_sets):
            raise _evidence_error(
                "EVALUATION_FAILED",
                "CP-10 wording rebuild execution identity is not independent",
                evidence_dir,
            )
        trigger_time = _timestamp(trigger.recorded_at)
        if any(
            _timestamp(record.prepared_at or "") <= trigger_time
            or _timestamp(record.recorded_at) <= trigger_time
            for record in cp10_reruns
        ):
            raise _evidence_error(
                "EVALUATION_FAILED",
                "CP-10 wording rebuild must be prepared and recorded after the trigger",
                evidence_dir,
            )

    superseded_ids = {run_id for record in records for run_id in record.supersedes_run_ids}
    if any(run_id not in record_map for run_id in superseded_ids):
        raise _evidence_error("EVALUATION_FAILED", "superseded run is missing", evidence_dir)

    for candidate in records:
        for superseded_id in candidate.supersedes_run_ids:
            source = record_map[superseded_id]
            if (
                candidate.change_proposal == "CP-10"
                and superseded_id in cp10_source_ids
            ):
                continue
            if source.rationale_review["status"] != "new-rationale":
                raise _evidence_error("EVALUATION_FAILED", "only new rationale runs may be superseded", evidence_dir)
            if candidate.case_id != source.case_id:
                raise _evidence_error("EVALUATION_FAILED", "superseding run must use the same case", evidence_dir)
            if candidate.outcome != "pass" or _timestamp(candidate.recorded_at) <= _timestamp(source.recorded_at):
                raise _evidence_error("EVALUATION_FAILED", "superseding run must be a later pass", evidence_dir)

    for record in records:
        if record.rationale_review["status"] != "new-rationale":
            continue
        if record.run_id in cp10_source_ids:
            continue
        proposal_id = record.rationale_review["change_proposal_id"]
        if not isinstance(proposal_id, str) or proposal_id.upper() not in approved_proposals:
            raise _evidence_error("EVALUATION_FAILED", "new rationale lacks an Approved change proposal", evidence_dir)
        if not any(
            record.run_id in candidate.supersedes_run_ids
            and candidate.outcome == "pass"
            and candidate.case_id == record.case_id
            and _timestamp(candidate.recorded_at) > _timestamp(record.recorded_at)
            for candidate in records
        ):
            raise _evidence_error("EVALUATION_FAILED", "new rationale lacks a superseding passing run", evidence_dir)
        case = case_map[record.case_id]
        if case.run_type == "wording":
            active_group_runs = [
                candidate
                for candidate in records
                if candidate.run_id not in superseded_ids
                and case_map[candidate.case_id].variant_group == case.variant_group
            ]
            if (
                len(active_group_runs) != 5
                or any(
                    candidate.outcome != "pass"
                    or _timestamp(candidate.recorded_at) <= _timestamp(record.recorded_at)
                    for candidate in active_group_runs
                )
            ):
                raise _evidence_error("EVALUATION_FAILED", "wording rationale was not rebuilt as 5/5 PASS", evidence_dir)

    selected_pairings: dict[str, dict[str, CaseSpec]] = {}
    for case in selected_cases:
        if case.run_type in {"baseline", "pressure"}:
            selected_pairings.setdefault(case.scenario_id, {})[case.run_type] = case
    for scenario_cases in selected_pairings.values():
        if set(scenario_cases) != {"baseline", "pressure"}:
            continue
        baseline_case = scenario_cases["baseline"]
        pressure_case = scenario_cases["pressure"]
        baseline_runs = [
            record
            for record in by_case.get(baseline_case.id, [])
            if record.run_id not in superseded_ids
        ]
        pressure_runs = [
            record
            for record in by_case.get(pressure_case.id, [])
            if record.run_id not in superseded_ids
        ]
        if len(baseline_runs) == 1 and len(pressure_runs) == 1:
            fingerprints = {
                (
                    record.schema_version,
                    record.client_id,
                    record.client_version,
                    record.model,
                    json.dumps(record.config, sort_keys=True),
                    record.runtime_surface,
                )
                for record in (baseline_runs[0], pressure_runs[0])
            }
            if len(fingerprints) != 1:
                raise _evidence_error(
                    "EVALUATION_FAILED",
                    f"pair environment changed for {baseline_case.scenario_id}",
                    evidence_dir,
                )

    baseline_observed = 0
    pressure_passed = 0
    wording_groups: dict[str, int] = {}
    level1_passed = 0
    level2_passed = 0
    effective_records = tuple(
        record for record in selected_records if record.run_id not in superseded_ids
    )
    blocked_runs = sum(record.outcome == "blocked" for record in effective_records)
    failed_runs = sum(record.outcome == "fail" for record in effective_records)

    def require(records_for_case: list[EvidenceRecord], expected_count: int, case: CaseSpec) -> None:
        if len(records_for_case) != expected_count or any(record.outcome == "blocked" for record in records_for_case):
            raise _evidence_error("EVALUATION_INCOMPLETE", f"case {case.id} is incomplete", evidence_dir)

    for case in selected_cases:
        records_for_case = [
            record for record in by_case.get(case.id, []) if record.run_id not in superseded_ids
        ]
        if case.run_type == "baseline":
            require(records_for_case, 1, case)
            record = records_for_case[0]
            if record.outcome != "observed":
                raise _evidence_error("EVALUATION_FAILED", f"baseline {case.id} is invalid", evidence_dir)
            baseline_observed += 1
        elif case.run_type == "pressure":
            require(records_for_case, 1, case)
            record = records_for_case[0]
            if record.outcome != "pass" or record.actual_decision != case.expected_decision:
                raise _evidence_error("EVALUATION_FAILED", f"pressure {case.id} did not pass", evidence_dir)
            pressure_passed += 1
        elif case.run_type == "wording":
            require(records_for_case, 5, case)
            if any(
                record.outcome != "pass" or record.actual_decision != case.expected_decision
                for record in records_for_case
            ):
                raise _evidence_error("EVALUATION_FAILED", f"wording {case.id} did not pass", evidence_dir)
            configurations = {
                (
                    record.schema_version,
                    record.client_id,
                    record.client_version,
                    record.model,
                    json.dumps(record.config, sort_keys=True),
                    record.runtime_surface,
                )
                for record in records_for_case
            }
            if len(configurations) != 1:
                raise _evidence_error("EVALUATION_FAILED", f"wording {case.id} configuration changed", evidence_dir)
            if any(record.schema_version == 2 for record in records_for_case):
                attempts = {record.attempt_id for record in records_for_case}
                sessions = {record.session_ref for record in records_for_case}
                timestamps = {record.recorded_at for record in records_for_case}
                if not all(len(values) == len(records_for_case) for values in (attempts, sessions, timestamps)):
                    raise _evidence_error(
                        "EVALUATION_FAILED",
                        f"wording {case.id} execution identity is not independent",
                        evidence_dir,
                    )
            wording_groups[case.variant_group or case.id] = len(records_for_case)
        elif case.run_type in {"level1", "level2"}:
            expected_clients = {
                client_id
                for client_id, client in clients.items()
                if client.level == (1 if case.run_type == "level1" else 2)
            }
            case_clients = {record.client_id for record in records_for_case}
            if any(record.outcome == "blocked" for record in records_for_case):
                raise _evidence_error("EVALUATION_INCOMPLETE", f"{case.run_type} client is blocked", evidence_dir)
            if case_clients != expected_clients or len(records_for_case) != len(expected_clients):
                raise _evidence_error("EVALUATION_INCOMPLETE", f"{case.run_type} clients are incomplete", evidence_dir)
            if any(
                record.outcome != "pass" or record.actual_decision != case.expected_decision
                for record in records_for_case
            ):
                raise _evidence_error("EVALUATION_FAILED", f"{case.run_type} client did not pass", evidence_dir)
            if case.run_type == "level1":
                level1_passed = len(records_for_case)
            else:
                level2_passed = len(records_for_case)

    return EvaluationSummary(
        baseline_observed,
        pressure_passed,
        wording_groups,
        level1_passed,
        level2_passed,
        blocked_runs,
        failed_runs,
        0,
    )


def _approved_change_proposals(registry_path: Path) -> set[str]:
    changes_dir = registry_path.resolve().parents[1] / "docs" / "changes"
    approved: set[str] = set()
    for path in changes_dir.glob("*.md"):
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        lines = content.splitlines()
        if not lines:
            continue
        heading = re.match(r"#\s+(CP-\d+)\b", lines[0], flags=re.IGNORECASE)
        if heading is None:
            continue
        metadata: dict[str, list[str]] = {}
        for line in lines[1:]:
            if line.startswith("## "):
                break
            match = re.fullmatch(
                r"-\s*(Status|状态|Gate Δ)\s*[：:]\s*(.+?)\s*",
                line,
                flags=re.IGNORECASE,
            )
            if match:
                metadata.setdefault(match.group(1).casefold(), []).append(
                    match.group(2)
                )
        status = metadata.get("status", []) + metadata.get("状态", [])
        gate = metadata.get("gate δ", [])
        if (
            len(status) != 1
            or len(gate) != 1
            or status[0].casefold() != "approved"
            or not re.fullmatch(
                r"Approved(?:\s+on\s+\d{4}-\d{2}-\d{2})?",
                gate[0],
                flags=re.IGNORECASE,
            )
        ):
            continue
        approved.add(heading.group(1).upper())
    return approved


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value[:-1] + "+00:00")


def _semantic_json_digest(path: Path) -> str:
    raw = _load_json(path, "EVIDENCE_INVALID")
    canonical = json.dumps(
        raw,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate tracing-spec-to-code M05 evaluation evidence.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    def add_common_paths(command: argparse.ArgumentParser) -> None:
        command.add_argument("--cases", type=Path, default=Path("evaluation/cases.json"))
        command.add_argument("--registry", type=Path, default=Path("tools/clients.json"))

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--case", required=True, dest="case_id")
    prepare.add_argument("--client", required=True, dest="client_id")
    prepare.add_argument("--run-id", required=True)
    prepare.add_argument("--rerun-of")
    prepare.add_argument("--change-proposal")
    add_common_paths(prepare)
    record = subparsers.add_parser("record")
    record.add_argument("--input", type=Path, required=True)
    record.add_argument("--evidence-dir", type=Path, default=Path("evaluation/evidence"))
    add_common_paths(record)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--evidence-dir", type=Path, default=Path("evaluation/evidence"))
    validate.add_argument("--run-type", action="append", choices=tuple(sorted(_RUN_TYPES)))
    add_common_paths(validate)
    summary = subparsers.add_parser("summary")
    summary.add_argument("--evidence-dir", type=Path, default=Path("evaluation/evidence"))
    summary.add_argument("--run-type", action="append", choices=tuple(sorted(_RUN_TYPES)))
    summary.add_argument("--format", choices=("json", "text"), default="text")
    add_common_paths(summary)
    return parser


def _summary_data(summary: EvaluationSummary) -> dict[str, object]:
    return {
        "baseline_observed": summary.baseline_observed,
        "pressure_passed": summary.pressure_passed,
        "wording_groups": summary.wording_groups,
        "level1_passed": summary.level1_passed,
        "level2_passed": summary.level2_passed,
        "blocked_runs": summary.blocked_runs,
        "failed_runs": summary.failed_runs,
        "open_rationales": summary.open_rationales,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    if arguments.command == "prepare":
        try:
            cases = {case.id: case for case in load_cases(arguments.cases)}
            case = cases.get(arguments.case_id)
            clients = {client.id for client in load_registry(arguments.registry)}
            if case is None or arguments.client_id not in clients:
                raise EvaluationError("CASE_INVALID", "case or client is unknown")
            if (
                case.run_type in _REFERENCE_RUN_TYPES
                and arguments.client_id != _REFERENCE_CLIENT
            ):
                raise EvaluationError(
                    "EVIDENCE_INVALID",
                    "reference cases must use Codex",
                )
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,79}", arguments.run_id):
                raise EvaluationError("EVIDENCE_INVALID", "run_id is invalid")
            if (arguments.rerun_of is None) != (arguments.change_proposal is None):
                raise EvaluationError(
                    "EVIDENCE_INVALID",
                    "--rerun-of and --change-proposal must be used together",
                )
            if arguments.rerun_of is not None and (
                not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,79}", arguments.rerun_of)
                or arguments.change_proposal not in {"CP-09", "CP-10"}
            ):
                raise EvaluationError("EVIDENCE_INVALID", "rerun metadata is invalid")
            if arguments.change_proposal == "CP-10" or (
                case.document_schema_version == 2 and case.id in _CP09_CASE_IDS
            ):
                mapping = (
                    _CP10_RERUN_MAPPING
                    if arguments.change_proposal == "CP-10"
                    else _CP09_RERUN_MAPPING
                )
                expected = mapping.get(arguments.run_id)
                if (
                    expected != (case.id, arguments.rerun_of)
                ):
                    raise EvaluationError(
                        "EVIDENCE_INVALID",
                        "canonical reference evidence requires an exact approved rerun mapping",
                    )
        except (DistributionError, EvaluationError) as error:
            code = error.code if isinstance(error, EvaluationError) else "EVIDENCE_INVALID"
            print(json.dumps({"code": code, "message": str(error)}))
            return 1
        template = {
            "schema_version": 2,
            "run_id": arguments.run_id,
            "case_id": case.id,
            "client_id": arguments.client_id,
            "skill_loaded": case.skill_loaded,
            "client_version": "",
            "model": "",
            "config": {},
            "runtime_surface": "",
            "attempt_id": f"attempt-{secrets.token_hex(16)}",
            "prepared_at": (
                datetime.now(timezone.utc)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
            ),
            "session_ref": "",
            "recorded_at": "",
            "prompt": case.prompt,
            "actual_decision": "",
            "verbatim_rationale": "",
            "outcome": "observed" if case.run_type == "baseline" else "pending",
            "reason": "",
            "notes": [],
            "rationale_review": {
                "status": "pending",
                "reviewer": "",
                "rule_refs": [],
                "change_proposal_id": None,
            },
            "supersedes_run_ids": (
                [arguments.rerun_of]
                if arguments.change_proposal == "CP-10"
                else []
            ),
            "rerun_of": arguments.rerun_of,
            "change_proposal": arguments.change_proposal,
        }
        print(json.dumps(template, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if arguments.command == "record":
        try:
            if not _is_repository_path(arguments.evidence_dir):
                raise EvaluationError("EVIDENCE_INVALID", "evidence_dir must stay inside the repository")
            written = record_evidence(
                arguments.input,
                arguments.evidence_dir,
                arguments.cases,
                arguments.registry,
            )
        except EvaluationError as error:
            print(json.dumps({"code": error.code, "message": str(error)}))
            return 1
        print(json.dumps({"path": written.as_posix()}))
        return 0
    if arguments.command in {"validate", "summary"}:
        try:
            summary = validate_suite(
                arguments.cases,
                arguments.registry,
                arguments.evidence_dir,
                set(arguments.run_type) if arguments.run_type else None,
            )
        except EvaluationError as error:
            print(json.dumps({"code": error.code, "message": str(error)}))
            return 1
        if arguments.command == "summary" and arguments.format == "text":
            print(
                "baseline={0} pressure={1} level1={2} level2={3}".format(
                    summary.baseline_observed,
                    summary.pressure_passed,
                    summary.level1_passed,
                    summary.level2_passed,
                )
            )
        else:
            print(json.dumps(_summary_data(summary), sort_keys=True))
        return 0
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
