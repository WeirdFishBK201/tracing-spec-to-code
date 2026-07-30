from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_git_checks import (
    PLAN_RELATIVE,
    prepare_repository,
    require_git,
    write_proposal,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = (
    REPO_ROOT
    / "skills"
    / "tracing-spec-to-code"
    / "scripts"
    / "tracing_spec_to_code.py"
)


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI_PATH), *arguments],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class CliBehaviorTests(unittest.TestCase):
    def test_valid_project_returns_zero_with_text_result(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"

        result = run_cli("validate", "--repo", str(fixture_root))

        self.assertEqual(0, result.returncode)
        self.assertIn("OK", result.stdout)
        self.assertEqual("", result.stderr)

    def test_validation_issue_returns_one_and_writes_text_to_stdout(self) -> None:
        fixture_root = (
            REPO_ROOT / "tests" / "fixtures" / "duplicate-requirement"
        )

        result = run_cli("validate", "--repo", str(fixture_root))

        self.assertEqual(1, result.returncode)
        self.assertIn("REQ_ID_DUPLICATE", result.stdout)
        self.assertIn("docs/specs/sample-spec.md:9", result.stdout)
        self.assertEqual("", result.stderr)

    def test_json_result_is_parseable_and_has_stable_fields(self) -> None:
        fixture_root = (
            REPO_ROOT / "tests" / "fixtures" / "unknown-reference"
        )

        result = run_cli(
            "validate",
            "--repo",
            str(fixture_root),
            "--format",
            "json",
        )

        self.assertEqual(1, result.returncode)
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            self.fail(f"stdout must contain JSON only: {error}")
        self.assertEqual({"issues", "valid"}, set(payload))
        self.assertFalse(payload["valid"])
        self.assertGreater(len(payload["issues"]), 0)
        self.assertTrue(
            all(
                set(issue) == {"code", "path", "line", "message"}
                for issue in payload["issues"]
            )
        )
        self.assertEqual("", result.stderr)

    def test_pending_workflow_gate_returns_one_with_stable_json_issue(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "valid-project"

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "valid-project"
            shutil.copytree(fixture_root, repo_root)
            plan_path = (
                repo_root
                / "docs"
                / "plans"
                / "sample-m01-contracts.md"
            )
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8").replace(
                    "- Gate P: Approved",
                    "- Gate P: Awaiting Approval",
                ),
                encoding="utf-8",
            )

            result = run_cli(
                "validate",
                "--repo",
                str(repo_root),
                "--format",
                "json",
            )

        self.assertEqual(1, result.returncode)
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            self.fail(f"stdout must contain JSON only: {error}")
        self.assertEqual({"issues", "valid"}, set(payload))
        self.assertFalse(payload["valid"])
        self.assertTrue(
            all(
                set(issue) == {"code", "path", "line", "message"}
                for issue in payload["issues"]
            )
        )
        self.assertTrue(
            any(
                issue["code"] == "GATE_APPROVAL_MISSING"
                and issue["path"]
                == "docs/plans/sample-m01-contracts.md"
                for issue in payload["issues"]
            )
        )
        self.assertEqual("", result.stderr)

    def test_invalid_config_returns_two_and_writes_diagnostic_to_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            (repo_root / ".tracing-spec-to-code.json").write_text(
                "{",
                encoding="utf-8",
            )

            result = run_cli("validate", "--repo", str(repo_root))

            self.assertEqual(2, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertIn("CFG_INVALID_JSON", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_invalid_argument_returns_two_with_usage_on_stderr(self) -> None:
        result = run_cli("validate", "--format", "xml")

        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("usage:", result.stderr)

    def test_missing_repository_returns_two_with_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_root = Path(temp_dir) / "does-not-exist"

            result = run_cli("validate", "--repo", str(missing_root))

            self.assertEqual(2, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertIn("repository directory does not exist", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_precommit_valid_state_returns_zero_with_stable_json(self) -> None:
        # Break caught: the precommit CLI cannot expose a machine-readable success.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)

            result = run_cli(
                "precommit",
                "--repo",
                str(repo_root),
                "--plan",
                PLAN_RELATIVE.as_posix(),
                "--format",
                "json",
            )

        self.assertEqual(0, result.returncode)
        self.assertEqual("", result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual({"issues": [], "valid": True}, payload)

    def test_precommit_issue_returns_one_on_stdout_with_json_schema(self) -> None:
        # Break caught: staged-scope blockers are misclassified as runtime failures.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            require_git(repo_root, "add", "--", "user-notes.txt")

            result = run_cli(
                "precommit",
                "--repo",
                str(repo_root),
                "--plan",
                PLAN_RELATIVE.as_posix(),
                "--format",
                "json",
            )

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual({"issues", "valid"}, set(payload))
        self.assertFalse(payload["valid"])
        self.assertTrue(
            any(
                issue["code"] == "STAGED_SCOPE_INVALID"
                for issue in payload["issues"]
            )
        )
        self.assertTrue(
            all(
                set(issue) == {"code", "path", "line", "message"}
                for issue in payload["issues"]
            )
        )

    def test_precommit_git_runtime_failure_returns_two_on_stderr(self) -> None:
        # Break caught: non-Git repositories produce a traceback or issue exit 1.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir, initialize_git=False)

            result = run_cli(
                "precommit",
                "--repo",
                str(repo_root),
                "--plan",
                PLAN_RELATIVE.as_posix(),
            )

        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertNotEqual("", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertNotIn("usage:", result.stderr)

    def test_precommit_malformed_plan_is_json_issue_not_runtime(self) -> None:
        # Break caught: deterministic artifact syntax defects are sent to stderr.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            plan_path = repo_root / PLAN_RELATIVE
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8").replace(
                    "## Tasks",
                    "## Work",
                ),
                encoding="utf-8",
            )
            require_git(repo_root, "add", "--", PLAN_RELATIVE.as_posix())

            result = run_cli(
                "precommit",
                "--repo",
                str(repo_root),
                "--plan",
                PLAN_RELATIVE.as_posix(),
                "--format",
                "json",
            )

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(
            any(
                issue["code"] == "ARTIFACT_PARSE_ERROR"
                for issue in payload["issues"]
            )
        )

    def test_precommit_malformed_proposal_metadata_is_json_issue(self) -> None:
        # Break caught: deterministic proposal metadata defects use runtime exit 2.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir, initialize_git=False)
            proposal = write_proposal(
                repo_root,
                proposal_id="CP-02",
                task_id="M01-T01",
            )
            proposal.write_text(
                proposal.read_text(encoding="utf-8").replace(
                    "- Affected tasks: M01-T01",
                    "- Affected tasks:",
                ),
                encoding="utf-8",
            )

            result = run_cli(
                "precommit",
                "--repo",
                str(repo_root),
                "--plan",
                PLAN_RELATIVE.as_posix(),
                "--format",
                "json",
            )

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(
            any(
                issue["code"] == "EVIDENCE_INCOMPLETE"
                and issue["path"].endswith(proposal.name)
                for issue in payload["issues"]
            )
        )


if __name__ == "__main__":
    unittest.main()
