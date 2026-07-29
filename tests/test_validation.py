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
        self.assertEqual({7, 9}, {issue.line for issue in unknown})
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
            self.assertEqual(15, unknown[0].line)
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
            self.assertEqual(11, missing[0].line)
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
            self.assertEqual(15, task_issue.line)
            self.assertEqual(
                Path("docs/specs/sample-spec.md"),
                coverage_issue.path,
            )
            self.assertEqual(11, coverage_issue.line)

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
