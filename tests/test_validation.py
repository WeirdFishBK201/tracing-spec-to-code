from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "tracing-spec-to-code" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from tstc.validation import validate_repository


class ValidateRepositoryTests(unittest.TestCase):
    def _copy_valid_project(self, temp_dir: str) -> Path:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"
        repo_root = Path(temp_dir).resolve()
        shutil.copytree(fixture_root, repo_root, dirs_exist_ok=True)
        return repo_root

    def test_missing_or_unknown_artifact_status_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = self._copy_valid_project(temp_dir)
            spec_path = repo_root / "docs/specs/sample-spec.md"
            spec_path.write_text(
                spec_path.read_text(encoding="utf-8").replace(
                    "- Status: Approved\n",
                    "",
                ),
                encoding="utf-8",
            )
            roadmap_path = repo_root / "docs/plans/sample-roadmap.md"
            roadmap_path.write_text(
                roadmap_path.read_text(encoding="utf-8").replace(
                    "- Status: Approved",
                    "- Status: Ready",
                ),
                encoding="utf-8",
            )

            issues = validate_repository(repo_root)

            invalid = [
                issue
                for issue in issues
                if issue.code == "WORKFLOW_STATUS_INVALID"
            ]
            self.assertEqual(2, len(invalid))
            self.assertEqual(
                {
                    Path("docs/specs/sample-spec.md"),
                    Path("docs/plans/sample-roadmap.md"),
                },
                {issue.path for issue in invalid},
            )

    def test_duplicate_status_metadata_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = self._copy_valid_project(temp_dir)
            spec_path = repo_root / "docs/specs/sample-spec.md"
            spec_path.write_text(
                spec_path.read_text(encoding="utf-8").replace(
                    "- Status: Approved",
                    "- Status: Approved\n- Status: Ready",
                ),
                encoding="utf-8",
            )

            issues = validate_repository(repo_root)

            invalid = [
                issue
                for issue in issues
                if issue.code == "WORKFLOW_STATUS_INVALID"
            ]
            self.assertEqual(1, len(invalid))
            self.assertEqual(
                Path("docs/specs/sample-spec.md"),
                invalid[0].path,
            )

    def test_missing_or_malformed_current_milestone_is_invalid(self) -> None:
        for replacement in ("", "- Current milestone: M1\n"):
            with self.subTest(replacement=replacement):
                with tempfile.TemporaryDirectory() as temp_dir:
                    repo_root = self._copy_valid_project(temp_dir)
                    roadmap_path = repo_root / "docs/plans/sample-roadmap.md"
                    roadmap_path.write_text(
                        roadmap_path.read_text(encoding="utf-8").replace(
                            "- Current milestone: M01\n",
                            replacement,
                        ),
                        encoding="utf-8",
                    )

                    issues = validate_repository(repo_root)

                    current = [
                        issue
                        for issue in issues
                        if issue.code == "CURRENT_MILESTONE_INVALID"
                    ]
                    self.assertEqual(1, len(current))
                    self.assertEqual(
                        Path("docs/plans/sample-roadmap.md"),
                        current[0].path,
                    )

    def test_current_milestone_metadata_is_only_allowed_on_roadmap(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = self._copy_valid_project(temp_dir)
            spec_path = repo_root / "docs/specs/sample-spec.md"
            spec_path.write_text(
                spec_path.read_text(encoding="utf-8").replace(
                    "- Gate S: Approved",
                    "- Gate S: Approved\n- Current milestone: M01",
                ),
                encoding="utf-8",
            )

            issues = validate_repository(repo_root)

            current = [
                issue
                for issue in issues
                if issue.code == "CURRENT_MILESTONE_INVALID"
            ]
            self.assertEqual(1, len(current))
            self.assertEqual(
                Path("docs/specs/sample-spec.md"),
                current[0].path,
            )

    def test_duplicate_current_milestone_metadata_fails_closed(self) -> None:
        for duplicate_value in ("M01", "M1"):
            with self.subTest(duplicate_value=duplicate_value):
                with tempfile.TemporaryDirectory() as temp_dir:
                    repo_root = self._copy_valid_project(temp_dir)
                    roadmap_path = repo_root / "docs/plans/sample-roadmap.md"
                    roadmap_path.write_text(
                        roadmap_path.read_text(encoding="utf-8").replace(
                            "- Current milestone: M01",
                            "- Current milestone: M01\n"
                            f"- Current milestone: {duplicate_value}",
                        ),
                        encoding="utf-8",
                    )

                    issues = validate_repository(repo_root)

                    current = [
                        issue
                        for issue in issues
                        if issue.code == "CURRENT_MILESTONE_INVALID"
                    ]
                    self.assertEqual(1, len(current))
                    self.assertEqual(
                        Path("docs/plans/sample-roadmap.md"),
                        current[0].path,
                    )

    def test_spec_roadmap_and_active_plan_require_approved_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = self._copy_valid_project(temp_dir)
            for relative_path, old, new in (
                (
                    "docs/specs/sample-spec.md",
                    "- Gate S: Approved",
                    "- Gate S: Pending",
                ),
                (
                    "docs/plans/sample-roadmap.md",
                    "- Gate P: Approved",
                    "- Gate P: Awaiting owner",
                ),
                (
                    "docs/plans/sample-m01-contracts.md",
                    "- Gate P: Approved",
                    "- Gate P: Rejected",
                ),
            ):
                path = repo_root / relative_path
                path.write_text(
                    path.read_text(encoding="utf-8").replace(old, new),
                    encoding="utf-8",
                )

            issues = validate_repository(repo_root)

            missing = [
                issue
                for issue in issues
                if issue.code == "GATE_APPROVAL_MISSING"
            ]
            self.assertEqual(3, len(missing))
            self.assertEqual(
                {"Gate S", "Gate P"},
                {
                    "Gate S" if "Gate S" in issue.message else "Gate P"
                    for issue in missing
                },
            )

    def test_two_active_plans_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = self._copy_valid_project(temp_dir)
            first_plan = repo_root / "docs/plans/sample-m01-contracts.md"
            second_plan = repo_root / "docs/plans/sample-m02-workflow.md"
            second_plan.write_text(
                first_plan.read_text(encoding="utf-8")
                .replace("M01", "M02")
                .replace("Contracts", "Workflow"),
                encoding="utf-8",
            )
            roadmap_path = repo_root / "docs/plans/sample-roadmap.md"
            roadmap_path.write_text(
                roadmap_path.read_text(encoding="utf-8")
                + "| M02 — Workflow | Add gates | REQ-SAMPLE-001 | "
                + "M01 | Unit tests |\n",
                encoding="utf-8",
            )

            issues = validate_repository(repo_root)

            multiple = [
                issue
                for issue in issues
                if issue.code == "PLAN_MULTIPLE_ACTIVE"
            ]
            self.assertEqual(1, len(multiple))
            self.assertEqual(
                Path("docs/plans/sample-m02-workflow.md"),
                multiple[0].path,
            )

    def test_unknown_plan_status_still_counts_as_active(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = self._copy_valid_project(temp_dir)
            first_plan = repo_root / "docs/plans/sample-m01-contracts.md"
            second_plan = repo_root / "docs/plans/sample-m02-workflow.md"
            second_plan.write_text(
                first_plan.read_text(encoding="utf-8")
                .replace("M01", "M02")
                .replace("Contracts", "Workflow")
                .replace(
                    "- Status: Approved — In Progress",
                    "- Status: Ready",
                ),
                encoding="utf-8",
            )
            roadmap_path = repo_root / "docs/plans/sample-roadmap.md"
            roadmap_path.write_text(
                roadmap_path.read_text(encoding="utf-8")
                + "| M02 — Workflow | Add gates | REQ-SAMPLE-001 | "
                + "M01 | Unit tests |\n",
                encoding="utf-8",
            )

            issues = validate_repository(repo_root)

            self.assertEqual(
                1,
                len(
                    [
                        issue
                        for issue in issues
                        if issue.code == "WORKFLOW_STATUS_INVALID"
                        and issue.path
                        == Path("docs/plans/sample-m02-workflow.md")
                    ]
                ),
            )
            self.assertEqual(
                1,
                len(
                    [
                        issue
                        for issue in issues
                        if issue.code == "PLAN_MULTIPLE_ACTIVE"
                    ]
                ),
            )

    def test_active_plan_must_match_current_and_next_milestone(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = self._copy_valid_project(temp_dir)
            roadmap_path = repo_root / "docs/plans/sample-roadmap.md"
            roadmap_path.write_text(
                roadmap_path.read_text(encoding="utf-8")
                .replace(
                    "- Current milestone: M01",
                    "- Current milestone: M02",
                )
                + "| M02 — Workflow | Add gates | REQ-SAMPLE-001 | "
                + "M01 | Unit tests |\n",
                encoding="utf-8",
            )

            issues = validate_repository(repo_root)

            not_next = [
                issue
                for issue in issues
                if issue.code == "PLAN_NOT_NEXT_MILESTONE"
            ]
            self.assertEqual(1, len(not_next))
            self.assertEqual(
                Path("docs/plans/sample-m01-contracts.md"),
                not_next[0].path,
            )

    def test_completed_plan_cannot_skip_an_incomplete_milestone(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = self._copy_valid_project(temp_dir)
            first_plan = repo_root / "docs/plans/sample-m01-contracts.md"
            future_plan = repo_root / "docs/plans/sample-m02-workflow.md"
            future_plan.write_text(
                first_plan.read_text(encoding="utf-8")
                .replace("M01", "M02")
                .replace("Contracts", "Workflow")
                .replace(
                    "- Status: Approved — In Progress",
                    "- Status: Completed",
                ),
                encoding="utf-8",
            )
            roadmap_path = repo_root / "docs/plans/sample-roadmap.md"
            roadmap_path.write_text(
                roadmap_path.read_text(encoding="utf-8")
                + "| M02 — Workflow | Add gates | REQ-SAMPLE-001 | "
                + "M01 | Unit tests |\n",
                encoding="utf-8",
            )

            issues = validate_repository(repo_root)

            not_next = [
                issue
                for issue in issues
                if issue.code == "PLAN_NOT_NEXT_MILESTONE"
            ]
            self.assertEqual(1, len(not_next))
            self.assertEqual(
                Path("docs/plans/sample-m02-workflow.md"),
                not_next[0].path,
            )

    def test_completed_prefix_allows_the_next_active_milestone(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = self._copy_valid_project(temp_dir)
            first_plan = repo_root / "docs/plans/sample-m01-contracts.md"
            first_content = first_plan.read_text(encoding="utf-8")
            first_plan.write_text(
                first_content.replace(
                    "- Status: Approved — In Progress",
                    "- Status: Completed",
                ),
                encoding="utf-8",
            )
            next_plan = repo_root / "docs/plans/sample-m02-workflow.md"
            next_plan.write_text(
                first_content
                .replace("M01", "M02")
                .replace("Contracts", "Workflow"),
                encoding="utf-8",
            )
            roadmap_path = repo_root / "docs/plans/sample-roadmap.md"
            roadmap_path.write_text(
                roadmap_path.read_text(encoding="utf-8")
                .replace(
                    "- Current milestone: M01",
                    "- Current milestone: M02",
                )
                + "| M02 — Workflow | Add gates | REQ-SAMPLE-001 | "
                + "M01 | Unit tests |\n",
                encoding="utf-8",
            )

            issues = validate_repository(repo_root)

            self.assertEqual([], issues)

    def test_awaiting_roadmap_allows_handoff_without_an_active_plan(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = self._copy_valid_project(temp_dir)
            plan_path = repo_root / "docs/plans/sample-m01-contracts.md"
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8").replace(
                    "- Status: Approved — In Progress",
                    "- Status: Completed",
                ),
                encoding="utf-8",
            )
            roadmap_path = repo_root / "docs/plans/sample-roadmap.md"
            roadmap_path.write_text(
                roadmap_path.read_text(encoding="utf-8")
                .replace(
                    "- Status: Approved",
                    "- Status: Awaiting Gate P — M02",
                )
                .replace(
                    "- Current milestone: M01",
                    "- Current milestone: M02",
                )
                + "| M02 — Workflow | Add gates | REQ-SAMPLE-001 | "
                + "M01 | Unit tests |\n",
                encoding="utf-8",
            )

            issues = validate_repository(repo_root)

            self.assertEqual([], issues)

    def test_missing_active_plan_for_next_milestone_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = self._copy_valid_project(temp_dir)
            plan_path = repo_root / "docs/plans/sample-m01-contracts.md"
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8").replace(
                    "- Status: Approved — In Progress",
                    "- Status: Completed",
                ),
                encoding="utf-8",
            )
            roadmap_path = repo_root / "docs/plans/sample-roadmap.md"
            roadmap_path.write_text(
                roadmap_path.read_text(encoding="utf-8")
                .replace(
                    "- Current milestone: M01",
                    "- Current milestone: M02",
                )
                + "| M02 — Workflow | Add gates | REQ-SAMPLE-001 | "
                + "M01 | Unit tests |\n",
                encoding="utf-8",
            )

            issues = validate_repository(repo_root)

            self.assertEqual(
                1,
                len(
                    [
                        issue
                        for issue in issues
                        if issue.code == "PLAN_NOT_NEXT_MILESTONE"
                    ]
                ),
            )

    def test_task_definition_count_must_be_between_two_and_five(self) -> None:
        for expected_count, should_report in ((1, True), (5, False), (6, True)):
            with self.subTest(expected_count=expected_count):
                with tempfile.TemporaryDirectory() as temp_dir:
                    repo_root = self._copy_valid_project(temp_dir)
                    plan_path = (
                        repo_root / "docs/plans/sample-m01-contracts.md"
                    )
                    content = plan_path.read_text(encoding="utf-8")
                    if expected_count == 1:
                        content = content.split(
                            "### M01-T02 — Check traceability"
                        )[0]
                    else:
                        for number in range(3, expected_count + 1):
                            content += (
                                f"\n### M01-T{number:02d} — Extra task\n\n"
                                "- Requirements: REQ-SAMPLE-001\n"
                            )
                    plan_path.write_text(content, encoding="utf-8")

                    issues = validate_repository(repo_root)

                    task_count = [
                        issue
                        for issue in issues
                        if issue.code == "TASK_COUNT_INVALID"
                    ]
                    self.assertEqual(int(should_report), len(task_count))
                    if should_report:
                        self.assertIn(
                            str(expected_count),
                            task_count[0].message,
                        )

    def test_task_like_heading_outside_tasks_does_not_satisfy_count(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = self._copy_valid_project(temp_dir)
            plan_path = repo_root / "docs/plans/sample-m01-contracts.md"
            content = plan_path.read_text(encoding="utf-8")
            content = content.split("### M01-T02 — Check traceability")[0]
            content += (
                "\n## Evidence\n\n"
                "### M01-T99 — Mentioned in evidence\n\n"
                "- Requirements: REQ-SAMPLE-002\n"
            )
            plan_path.write_text(content, encoding="utf-8")

            issues = validate_repository(repo_root)

            task_count = [
                issue
                for issue in issues
                if issue.code == "TASK_COUNT_INVALID"
            ]
            self.assertEqual(1, len(task_count))
            self.assertIn("found 1", task_count[0].message)

    def test_new_h1_resets_tasks_section_before_task_like_heading(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = self._copy_valid_project(temp_dir)
            plan_path = repo_root / "docs/plans/sample-m01-contracts.md"
            content = plan_path.read_text(encoding="utf-8")
            content = content.split("### M01-T02 — Check traceability")[0]
            content += (
                "\n# Appendix\n\n"
                "### M01-T99 — Mentioned outside the plan\n\n"
                "- Requirements: REQ-SAMPLE-002\n"
            )
            plan_path.write_text(content, encoding="utf-8")

            issues = validate_repository(repo_root)

            task_count = [
                issue
                for issue in issues
                if issue.code == "TASK_COUNT_INVALID"
            ]
            self.assertEqual(1, len(task_count))
            self.assertIn("found 1", task_count[0].message)

    def test_change_proposal_requires_approved_status_and_gate_delta(
        self,
    ) -> None:
        for old, new in (
            ("- Status: Approved", "- Status: Pending Gate Δ"),
            ("- Gate Δ: Approved", "- Gate Δ: Pending"),
        ):
            with self.subTest(new=new):
                with tempfile.TemporaryDirectory() as temp_dir:
                    repo_root = self._copy_valid_project(temp_dir)
                    proposal_path = (
                        repo_root
                        / "docs/changes/sample-cp01-traceability.md"
                    )
                    proposal_path.write_text(
                        proposal_path.read_text(encoding="utf-8").replace(
                            old,
                            new,
                        ),
                        encoding="utf-8",
                    )

                    issues = validate_repository(repo_root)

                    pending = [
                        issue
                        for issue in issues
                        if issue.code == "CHANGE_PROPOSAL_PENDING"
                    ]
                    self.assertEqual(1, len(pending))
                    self.assertEqual(
                        Path(
                            "docs/changes/sample-cp01-traceability.md"
                        ),
                        pending[0].path,
                    )

    def test_valid_project_has_no_issues(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"

        issues = validate_repository(fixture_root)

        self.assertEqual([], issues)

    def test_duplicate_requirement_reports_second_definition(self) -> None:
        fixture_root = (
            REPO_ROOT / "tests" / "fixtures" / "duplicate-requirement"
        )

        issues = validate_repository(fixture_root)

        duplicates = [
            issue for issue in issues if issue.code == "REQ_ID_DUPLICATE"
        ]
        self.assertEqual(1, len(duplicates))
        self.assertEqual(
            Path("docs/specs/sample-spec.md"),
            duplicates[0].path,
        )
        self.assertEqual(9, duplicates[0].line)
        self.assertIn("REQ-SAMPLE-001", duplicates[0].message)

    def test_unknown_requirement_references_are_reported_at_each_use(self) -> None:
        fixture_root = (
            REPO_ROOT / "tests" / "fixtures" / "unknown-reference"
        )

        issues = validate_repository(fixture_root)

        unknown = [
            issue for issue in issues if issue.code == "REQ_REFERENCE_UNKNOWN"
        ]
        self.assertEqual(2, len(unknown))
        self.assertEqual(
            {
                Path("docs/plans/sample-roadmap.md"),
                Path("docs/plans/sample-m01-contracts.md"),
            },
            {issue.path for issue in unknown},
        )
        self.assertEqual({11}, {issue.line for issue in unknown})
        self.assertTrue(
            all("REQ-SAMPLE-999" in issue.message for issue in unknown)
        )

    def test_non_spec_heading_cannot_define_an_unknown_requirement(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            shutil.copytree(fixture_root, repo_root, dirs_exist_ok=True)
            proposal_path = (
                repo_root
                / "docs/changes/sample-cp01-traceability.md"
            )
            proposal_path.write_text(
                proposal_path.read_text(encoding="utf-8")
                + "\n### REQ-SAMPLE-999 — Not a specification definition\n",
                encoding="utf-8",
            )

            issues = validate_repository(repo_root)

            unknown = [
                issue
                for issue in issues
                if issue.code == "REQ_REFERENCE_UNKNOWN"
            ]
            self.assertEqual(1, len(unknown))
            self.assertEqual(
                Path("docs/changes/sample-cp01-traceability.md"),
                unknown[0].path,
            )
            self.assertEqual(16, unknown[0].line)
            self.assertIn("REQ-SAMPLE-999", unknown[0].message)

    def test_invalid_ids_and_duplicate_task_are_reported(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            shutil.copytree(fixture_root, repo_root, dirs_exist_ok=True)
            spec_path = repo_root / "docs/specs/sample-spec.md"
            spec_path.write_text(
                spec_path.read_text(encoding="utf-8").replace(
                    "### REQ-SAMPLE-002",
                    "### REQ-SAMPLE-2",
                ),
                encoding="utf-8",
            )
            plan_path = repo_root / "docs/plans/sample-m01-contracts.md"
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8").replace(
                    "### M01-T02",
                    "### M01-T01",
                )
                + "\n### M1-T1 — Invalid task ID\n\n"
                + "- Requirements: REQ-SAMPLE-001\n",
                encoding="utf-8",
            )

            issues = validate_repository(repo_root)

            issues_by_code = {
                code: [issue for issue in issues if issue.code == code]
                for code in {
                    "REQ_ID_INVALID",
                    "TASK_ID_INVALID",
                    "TASK_ID_DUPLICATE",
                }
            }
            self.assertTrue(
                all(len(found) == 1 for found in issues_by_code.values())
            )
            self.assertEqual(
                Path("docs/specs/sample-spec.md"),
                issues_by_code["REQ_ID_INVALID"][0].path,
            )
            self.assertTrue(
                all(
                    issue.line > 0
                    for found in issues_by_code.values()
                    for issue in found
                )
            )

    def test_missing_spec_reports_only_artifact_missing(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            shutil.copytree(fixture_root, repo_root, dirs_exist_ok=True)
            (repo_root / "docs/specs/sample-spec.md").unlink()

            issues = validate_repository(repo_root)

            self.assertEqual(
                ["ARTIFACT_MISSING"],
                [issue.code for issue in issues],
            )
            self.assertEqual(
                Path("docs/specs/sample-spec.md"),
                issues[0].path,
            )
            self.assertEqual(0, issues[0].line)

    def test_parse_error_is_returned_as_validation_issue(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            shutil.copytree(fixture_root, repo_root, dirs_exist_ok=True)
            plan_path = repo_root / "docs/plans/sample-m01-contracts.md"
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8").replace(
                    "## Tasks",
                    "## Work",
                ),
                encoding="utf-8",
            )

            try:
                issues = validate_repository(repo_root)
            except Exception as error:
                self.fail(f"parse errors must become ValidationIssue: {error}")

            self.assertEqual(1, len(issues))
            self.assertEqual("ARTIFACT_PARSE_ERROR", issues[0].code)
            self.assertEqual(
                Path("docs/plans/sample-m01-contracts.md"),
                issues[0].path,
            )
            self.assertEqual(1, issues[0].line)

    def test_missing_roadmap_reference_points_to_requirement_definition(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            shutil.copytree(fixture_root, repo_root, dirs_exist_ok=True)
            roadmap_path = repo_root / "docs/plans/sample-roadmap.md"
            roadmap_path.write_text(
                roadmap_path.read_text(encoding="utf-8").replace(
                    "REQ-SAMPLE-001, REQ-SAMPLE-002",
                    "REQ-SAMPLE-001",
                ),
                encoding="utf-8",
            )

            issues = validate_repository(repo_root)

            missing = [
                issue
                for issue in issues
                if issue.code == "REQ_REFERENCE_MISSING"
            ]
            self.assertEqual(1, len(missing))
            self.assertEqual(
                Path("docs/specs/sample-spec.md"),
                missing[0].path,
            )
            self.assertEqual(14, missing[0].line)
            self.assertIn("roadmap", missing[0].message)
            self.assertIn("REQ-SAMPLE-002", missing[0].message)

    def test_roadmap_prose_does_not_replace_milestone_mapping(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            shutil.copytree(fixture_root, repo_root, dirs_exist_ok=True)
            roadmap_path = repo_root / "docs/plans/sample-roadmap.md"
            roadmap_path.write_text(
                roadmap_path.read_text(encoding="utf-8").replace(
                    "REQ-SAMPLE-001, REQ-SAMPLE-002",
                    "REQ-SAMPLE-001",
                )
                + "\n## Notes\n\n"
                + "Mentioned without milestone mapping: REQ-SAMPLE-002.\n",
                encoding="utf-8",
            )

            issues = validate_repository(repo_root)

            missing = [
                issue
                for issue in issues
                if issue.code == "REQ_REFERENCE_MISSING"
            ]
            self.assertEqual(1, len(missing))
            self.assertEqual(
                Path("docs/specs/sample-spec.md"),
                missing[0].path,
            )
            self.assertIn("REQ-SAMPLE-002", missing[0].message)

    def test_task_without_known_requirement_reports_task_and_plan_coverage(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            shutil.copytree(fixture_root, repo_root, dirs_exist_ok=True)
            plan_path = repo_root / "docs/plans/sample-m01-contracts.md"
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8").replace(
                    "- Requirements: REQ-SAMPLE-002",
                    "- Requirements: none",
                ),
                encoding="utf-8",
            )

            issues = validate_repository(repo_root)

            missing = [
                issue
                for issue in issues
                if issue.code == "REQ_REFERENCE_MISSING"
            ]
            self.assertEqual(2, len(missing))
            task_issue = next(
                issue for issue in missing if "M01-T02" in issue.message
            )
            coverage_issue = next(
                issue for issue in missing if "REQ-SAMPLE-002" in issue.message
            )
            self.assertEqual(
                Path("docs/plans/sample-m01-contracts.md"),
                task_issue.path,
            )
            self.assertEqual(17, task_issue.line)
            self.assertEqual(
                Path("docs/specs/sample-spec.md"),
                coverage_issue.path,
            )
            self.assertEqual(14, coverage_issue.line)

    def test_reference_after_task_section_does_not_cover_task(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            shutil.copytree(fixture_root, repo_root, dirs_exist_ok=True)
            plan_path = repo_root / "docs/plans/sample-m01-contracts.md"
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8").replace(
                    "- Requirements: REQ-SAMPLE-002",
                    "- Requirements: none",
                )
                + "\n## Evidence\n\n"
                + "- Requirements: REQ-SAMPLE-002\n",
                encoding="utf-8",
            )

            issues = validate_repository(repo_root)

            missing = [
                issue
                for issue in issues
                if issue.code == "REQ_REFERENCE_MISSING"
            ]
            self.assertEqual(2, len(missing))
            self.assertTrue(
                any("M01-T02" in issue.message for issue in missing)
            )
            self.assertTrue(
                any("REQ-SAMPLE-002" in issue.message for issue in missing)
            )

    def test_issues_are_stably_sorted_by_path_line_and_code(self) -> None:
        fixture_root = (
            REPO_ROOT / "tests" / "fixtures" / "unknown-reference"
        )

        first = validate_repository(fixture_root)
        second = validate_repository(fixture_root)
        first_keys = [
            (issue.path.as_posix().casefold(), issue.line, issue.code)
            for issue in first
        ]
        second_keys = [
            (issue.path.as_posix().casefold(), issue.line, issue.code)
            for issue in second
        ]

        self.assertEqual(sorted(first_keys), first_keys)
        self.assertEqual(first_keys, second_keys)

    def test_future_milestone_requirement_does_not_need_current_plan_task(
        self,
    ) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            shutil.copytree(fixture_root, repo_root, dirs_exist_ok=True)
            spec_path = repo_root / "docs/specs/sample-spec.md"
            spec_path.write_text(
                spec_path.read_text(encoding="utf-8")
                + "\n### REQ-SAMPLE-003 — Future workflow\n\n"
                + "Implemented in a future milestone.\n",
                encoding="utf-8",
            )
            roadmap_path = repo_root / "docs/plans/sample-roadmap.md"
            roadmap_path.write_text(
                roadmap_path.read_text(encoding="utf-8")
                + "| M02 — Workflow | Future workflow | "
                + "REQ-SAMPLE-003 | M01 | Workflow tests |\n",
                encoding="utf-8",
            )

            issues = validate_repository(repo_root)

            self.assertEqual([], issues)

    def test_requirement_coverage_table_assigns_current_milestone(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            shutil.copytree(fixture_root, repo_root, dirs_exist_ok=True)
            roadmap_path = repo_root / "docs/plans/sample-roadmap.md"
            roadmap_path.write_text(
                roadmap_path.read_text(encoding="utf-8").replace(
                    "REQ-SAMPLE-001, REQ-SAMPLE-002",
                    "REQ-SAMPLE-001",
                )
                + "\n## Requirement coverage\n\n"
                + "| Requirement | Milestone |\n"
                + "|---|---|\n"
                + "| REQ-SAMPLE-001 | M01 |\n"
                + "| REQ-SAMPLE-002 | M01 |\n",
                encoding="utf-8",
            )
            plan_path = repo_root / "docs/plans/sample-m01-contracts.md"
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8").replace(
                    "- Requirements: REQ-SAMPLE-002",
                    "- Requirements: none",
                ),
                encoding="utf-8",
            )

            issues = validate_repository(repo_root)

            missing = [
                issue
                for issue in issues
                if issue.code == "REQ_REFERENCE_MISSING"
            ]
            self.assertEqual(2, len(missing))
            self.assertTrue(
                any("M01-T02" in issue.message for issue in missing)
            )
            self.assertTrue(
                any("REQ-SAMPLE-002" in issue.message for issue in missing)
            )


if __name__ == "__main__":
    unittest.main()
