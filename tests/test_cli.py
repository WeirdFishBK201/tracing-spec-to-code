from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
