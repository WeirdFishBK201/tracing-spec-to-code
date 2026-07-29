from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "tracing-spec-to-code" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from tstc.config import load_config
from tstc.artifacts import ArtifactKind, ArtifactParseError, discover_artifacts


class DiscoverArtifactsTests(unittest.TestCase):
    def test_discovers_default_artifacts_and_parses_definitions(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"

        artifacts = discover_artifacts(load_config(fixture_root))

        self.assertEqual(4, len(artifacts))
        by_kind = {artifact.kind: artifact for artifact in artifacts}
        self.assertEqual(
            ("REQ-SAMPLE-001", "REQ-SAMPLE-002"),
            by_kind[ArtifactKind.SPEC].requirement_ids,
        )
        self.assertEqual(
            ("REQ-SAMPLE-001", "REQ-SAMPLE-002"),
            by_kind[ArtifactKind.ROADMAP].referenced_ids,
        )
        self.assertEqual(
            ("M01-T01", "M01-T02"),
            by_kind[ArtifactKind.MILESTONE_PLAN].task_ids,
        )
        self.assertEqual(
            ("REQ-SAMPLE-001", "REQ-SAMPLE-002"),
            by_kind[ArtifactKind.MILESTONE_PLAN].referenced_ids,
        )
        self.assertEqual(
            ("REQ-SAMPLE-002", "M01-T02"),
            by_kind[ArtifactKind.CHANGE_PROPOSAL].referenced_ids,
        )

    def test_discovers_artifacts_with_custom_filename_templates(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            shutil.copytree(fixture_root / "docs", repo_root / "docs")
            (repo_root / "docs/specs/sample-spec.md").rename(
                repo_root / "docs/specs/spec-sample.md"
            )
            (repo_root / "docs/plans/sample-roadmap.md").rename(
                repo_root / "docs/plans/roadmap-sample.md"
            )
            (repo_root / "docs/plans/sample-m01-contracts.md").rename(
                repo_root / "docs/plans/m01-sample-contracts.md"
            )
            (repo_root / "docs/changes/sample-cp01-traceability.md").rename(
                repo_root / "docs/changes/cp01-sample-traceability.md"
            )
            (repo_root / ".tracing-spec-to-code.json").write_text(
                json.dumps(
                    {
                        "feature_slug": "sample",
                        "spec_filename_template": "spec-{feature}.md",
                        "roadmap_filename_template": "roadmap-{feature}.md",
                        "milestone_plan_filename_template": (
                            "m{milestone}-{feature}-{milestone_slug}.md"
                        ),
                        "change_proposal_filename_template": (
                            "cp{proposal}-{feature}-{proposal_slug}.md"
                        ),
                    }
                ),
                encoding="utf-8",
            )

            artifacts = discover_artifacts(load_config(repo_root))

            self.assertEqual(
                {
                    "spec-sample.md",
                    "roadmap-sample.md",
                    "m01-sample-contracts.md",
                    "cp01-sample-traceability.md",
                },
                {artifact.path.name for artifact in artifacts},
            )

    def test_missing_required_section_reports_parse_error(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            shutil.copytree(fixture_root, repo_root, dirs_exist_ok=True)
            spec_path = repo_root / "docs/specs/sample-spec.md"
            spec_path.write_text(
                spec_path.read_text(encoding="utf-8").replace(
                    "## Requirements",
                    "## Notes",
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ArtifactParseError) as raised:
                discover_artifacts(load_config(repo_root))

            self.assertEqual("ARTIFACT_PARSE_ERROR", raised.exception.code)
            self.assertEqual(spec_path, raised.exception.path)
            self.assertEqual(1, raised.exception.line)

    def test_milestone_plan_requires_milestone_metadata(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            shutil.copytree(fixture_root, repo_root, dirs_exist_ok=True)
            plan_path = repo_root / "docs/plans/sample-m01-contracts.md"
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8").replace(
                    "- Milestone: M01 — Contracts\n\n",
                    "",
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ArtifactParseError) as raised:
                discover_artifacts(load_config(repo_root))

            self.assertEqual("ARTIFACT_PARSE_ERROR", raised.exception.code)
            self.assertEqual(plan_path, raised.exception.path)
            self.assertEqual(1, raised.exception.line)
            self.assertIn("milestone metadata", raised.exception.message)

    def test_requirement_coverage_expands_milestone_range(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            shutil.copytree(fixture_root, repo_root, dirs_exist_ok=True)
            roadmap_path = repo_root / "docs/plans/sample-roadmap.md"
            roadmap_path.write_text(
                roadmap_path.read_text(encoding="utf-8")
                + "\n## Requirement coverage\n\n"
                + "| Requirement | Milestone |\n"
                + "|---|---|\n"
                + "| REQ-SAMPLE-002 | M01–M03 |\n",
                encoding="utf-8",
            )

            artifacts = discover_artifacts(load_config(repo_root))

            roadmap = next(
                artifact
                for artifact in artifacts
                if artifact.kind == ArtifactKind.ROADMAP
            )
            mapped = {
                ref.milestone_id
                for ref in roadmap.milestone_refs
                if "REQ-SAMPLE-002" in ref.requirement_ids
            }
            self.assertEqual({"M01", "M02", "M03"}, mapped)

    def test_requirement_id_is_not_misread_as_milestone_cell(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            shutil.copytree(fixture_root, repo_root, dirs_exist_ok=True)
            roadmap_path = repo_root / "docs/plans/sample-roadmap.md"
            roadmap_path.write_text(
                roadmap_path.read_text(encoding="utf-8")
                + "\n## Requirement coverage\n\n"
                + "| Requirement | Milestone |\n"
                + "|---|---|\n"
                + "| REQ-M01-999 | M02 |\n",
                encoding="utf-8",
            )

            artifacts = discover_artifacts(load_config(repo_root))

            roadmap = next(
                artifact
                for artifact in artifacts
                if artifact.kind == ArtifactKind.ROADMAP
            )
            mapped = {
                ref.milestone_id
                for ref in roadmap.milestone_refs
                if "REQ-M01-999" in ref.requirement_ids
            }
            self.assertEqual({"M02"}, mapped)


if __name__ == "__main__":
    unittest.main()
