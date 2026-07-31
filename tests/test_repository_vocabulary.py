from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
M06_PLAN = REPO_ROOT / "docs/plans/tracing-spec-to-code-m06-readable-localized-terminology.md"
TEXT_SUFFIXES = {".md", ".json", ".py", ".yaml", ".yml"}
ALLOWED_LOCALIZED_LABELS = {"需求确认", "实施批准", "变更批准", "变更申请"}
LEGACY_PATTERNS = (
    re.compile(r"\bGate S\b"),
    re.compile(r"\bGate P\b"),
    re.compile(r"\bGate Δ\b"),
    re.compile(r"change[ -]proposal", re.IGNORECASE),
    re.compile(r"\bchange_proposal\b"),
    re.compile(r"\bCP-\d+\b", re.IGNORECASE),
    re.compile(r"(?:^|[-_/])cp\d{2}(?:[-_/]|\.|$)", re.IGNORECASE),
)


class RepositoryVocabularyTests(unittest.TestCase):
    def _scannable_text(self, path: Path) -> str:
        text = path.read_text(encoding="utf-8")
        if path != M06_PLAN:
            return text
        lines: list[str] = []
        in_commit_scope = False
        for line in text.splitlines():
            if line.startswith("### Commit scope"):
                in_commit_scope = True
            elif in_commit_scope and line.startswith("### "):
                in_commit_scope = False
            if not in_commit_scope:
                lines.append(line)
        return "\n".join(lines)

    def _text_files(self) -> list[Path]:
        completed = subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={REPO_ROOT.as_posix()}",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return [
            REPO_ROOT / relative_path
            for relative_path in completed.stdout.splitlines()
            if relative_path
            and (REPO_ROOT / relative_path).is_file()
            and (REPO_ROOT / relative_path).suffix.lower() in TEXT_SUFFIXES
            and (REPO_ROOT / relative_path) != Path(__file__).resolve()
        ]

    def test_current_tree_has_no_superseded_workflow_vocabulary(self) -> None:
        findings: list[str] = []
        for path in self._text_files():
            try:
                text = self._scannable_text(path)
            except UnicodeDecodeError:
                continue
            for pattern in LEGACY_PATTERNS:
                if pattern.search(text):
                    findings.append(f"{path.relative_to(REPO_ROOT)}: {pattern.pattern}")
        self.assertEqual([], findings)

    def test_maintained_markdown_uses_english_except_exact_labels(self) -> None:
        findings: list[str] = []
        for path in self._text_files():
            if path.suffix.lower() != ".md":
                continue
            text = self._scannable_text(path)
            han_runs = set(re.findall(r"[\u3400-\u9fff]+", text))
            unexpected = han_runs - ALLOWED_LOCALIZED_LABELS
            if unexpected:
                findings.append(f"{path.relative_to(REPO_ROOT)}: {sorted(unexpected)}")
        self.assertEqual([], findings)

    def test_current_tree_contains_canonical_machine_contract(self) -> None:
        completed = subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={REPO_ROOT.as_posix()}",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        paths = {line for line in completed.stdout.splitlines() if line}
        self.assertIn("skills/tracing-spec-to-code/scripts/tstc/artifacts.py", paths)
        contract_text = "\n".join(
            (REPO_ROOT / path).read_text(encoding="utf-8")
            for path in paths
            if Path(path).suffix.lower() in TEXT_SUFFIXES
            and (REPO_ROOT / path).is_file()
        )
        for key in (
            "requirements_confirmation",
            "implementation_approval",
            "change_approval",
            "change_request",
            "change_request_id",
            "approved_change_requests",
            "Change-Requests",
        ):
            self.assertIn(key, contract_text)


if __name__ == "__main__":
    unittest.main()
