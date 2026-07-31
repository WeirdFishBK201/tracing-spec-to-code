from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "tracing-spec-to-code" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from tstc.artifacts import (
    ArtifactKind,
    ArtifactRef,
    IdOccurrence,
)
from tstc.evidence import (
    parse_evidence,
    validate_evidence,
)


COMPLETE_PLAN = """\
# Sample M03 Evidence Plan

- Status: Approved — In Progress
- Milestone: M03 — Evidence and commit
- Requirements: REQ-SAMPLE-010, REQ-SAMPLE-016
- Implementation approval: Approved

## Tasks

### M03-T01 — Parse evidence

- Requirements: REQ-SAMPLE-010

### M03-T02 — Check evidence

- Requirements: REQ-SAMPLE-016

## Traceability

| Task | Requirements | Implementation | Tests |
|---|---|---|---|
| `M03-T01` | `REQ-SAMPLE-010` | `src/evidence.py` | `tests/test_evidence.py::test_parse` |
| `M03-T02` | `REQ-SAMPLE-016` | `src/checks.py` | `tests/test_evidence.py::test_validate` |

## Evidence and commit

### Task status

| Task | Status | Actual verification |
|---|---|---|
| `M03-T01` | `Completed` | `tests.test_evidence`: 8/8 PASS |
| `M03-T02` | `Completed` | `tests.test_evidence`: 8/8 PASS |

- Approved Change Requests: CR-05
- Deviations: None
- Baseline dirty paths: None

### Verification

| Scope | Command | Expected | Actual | Result |
|---|---|---|---|---|
| Targeted | `python -m unittest tests.test_evidence -v` | All pass | 8/8 pass | PASS |
| Broader | `python -m unittest discover -s tests -v` | All pass | 70/70 pass | PASS |

### Commit scope

| Path | Purpose |
|---|---|
| `src/evidence.py` | Evidence parser |
| `src/checks.py` | Evidence validation |
| `tests/test_evidence.py` | Behavior tests |

### Commit draft

```text
feat(evidence): validate milestone evidence

Milestone: M03 Evidence and commit
Requirements: REQ-SAMPLE-010, REQ-SAMPLE-016
Change-Requests: CR-05
```
"""


class EvidenceTests(unittest.TestCase):
    def _write_plan(
        self,
        temp_dir: str,
        content: str = COMPLETE_PLAN,
    ) -> tuple[Path, Path]:
        repo_root = Path(temp_dir).resolve()
        plan_path = repo_root / "docs/plans/sample-m03-evidence.md"
        plan_path.parent.mkdir(parents=True)
        plan_path.write_text(content, encoding="utf-8")
        return repo_root, plan_path

    def _known_plan(self, plan_path: Path) -> ArtifactRef:
        return ArtifactRef(
            kind=ArtifactKind.MILESTONE_PLAN,
            path=plan_path,
            requirement_ids=(),
            task_ids=("M03-T01", "M03-T02"),
            referenced_ids=("REQ-SAMPLE-010", "REQ-SAMPLE-016"),
            occurrences=(
                IdOccurrence(
                    value="M03-T01",
                    category="task",
                    line=9,
                    is_definition=True,
                    is_valid=True,
                    section_end_line=13,
                ),
                IdOccurrence(
                    value="REQ-SAMPLE-010",
                    category="requirement",
                    line=11,
                    is_definition=False,
                    is_valid=True,
                ),
                IdOccurrence(
                    value="M03-T02",
                    category="task",
                    line=13,
                    is_definition=True,
                    is_valid=True,
                    section_end_line=17,
                ),
                IdOccurrence(
                    value="REQ-SAMPLE-016",
                    category="requirement",
                    line=15,
                    is_definition=False,
                    is_valid=True,
                ),
            ),
            milestone_id="M03",
        )

    def _parse_and_validate(
        self,
        temp_dir: str,
        content: str = COMPLETE_PLAN,
        approved_change_requests: tuple[str, ...] = ("CR-05",),
    ):
        repo_root, plan_path = self._write_plan(temp_dir, content)
        record = parse_evidence(repo_root, plan_path)
        issues = validate_evidence(
            record,
            self._known_plan(plan_path),
            approved_change_requests,
        )
        return record, issues

    def test_complete_canonical_evidence_is_parsed_and_valid(self) -> None:
        # Break caught: an empty or prose-scanning parser loses canonical rows.
        with tempfile.TemporaryDirectory() as temp_dir:
            record, issues = self._parse_and_validate(temp_dir)

        self.assertEqual("M03", record.milestone_id)
        self.assertEqual(
            ("M03-T01", "M03-T02"),
            tuple(row.task_id for row in record.traceability),
        )
        self.assertEqual(
            ("M03-T01", "M03-T02"),
            tuple(row.task_id for row in record.task_statuses),
        )
        self.assertEqual(
            ("Targeted", "Broader"),
            tuple(row.scope for row in record.verifications),
        )
        self.assertEqual(("CR-05",), record.approved_change_requests)
        self.assertEqual((), record.deviations)
        self.assertEqual((), record.baseline_dirty_paths)
        self.assertEqual(
            (
                "src/evidence.py",
                "src/checks.py",
                "tests/test_evidence.py",
            ),
            tuple(row.path for row in record.commit_scope),
        )
        self.assertTrue(
            record.commit_message.startswith(
                "feat(evidence): validate milestone evidence"
            )
        )
        self.assertEqual([], issues)

    def test_traceability_rejects_missing_duplicate_and_unknown_tasks(
        self,
    ) -> None:
        # Break caught: set-only comparison hides duplicate or unknown task rows.
        mutations = {
            "missing": (
                "| `M03-T02` | `REQ-SAMPLE-016` | `src/checks.py` | "
                "`tests/test_evidence.py::test_validate` |\n",
                "",
            ),
            "duplicate": (
                "| `M03-T02` | `REQ-SAMPLE-016` | `src/checks.py` | "
                "`tests/test_evidence.py::test_validate` |",
                "| `M03-T01` | `REQ-SAMPLE-016` | `src/checks.py` | "
                "`tests/test_evidence.py::test_validate` |",
            ),
            "unknown": (
                "| `M03-T02` | `REQ-SAMPLE-016` | `src/checks.py` | "
                "`tests/test_evidence.py::test_validate` |",
                "| `M03-T99` | `REQ-SAMPLE-016` | `src/checks.py` | "
                "`tests/test_evidence.py::test_validate` |",
            ),
        }
        for label, (old, new) in mutations.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(
                        temp_dir,
                        COMPLETE_PLAN.replace(old, new),
                    )

                evidence = [
                    issue
                    for issue in issues
                    if issue.code == "EVIDENCE_INCOMPLETE"
                ]
                self.assertTrue(evidence)
                self.assertTrue(
                    any("traceability task" in issue.message for issue in evidence)
                )

    def test_task_status_rejects_missing_duplicate_unknown_and_incomplete(
        self,
    ) -> None:
        # Break caught: a task can reach commit without exactly one Completed row.
        replacements = {
            "missing": (
                "| `M03-T02` | `Completed` | "
                "`tests.test_evidence`: 8/8 PASS |\n",
                "",
            ),
            "duplicate": (
                "| `M03-T02` | `Completed` | "
                "`tests.test_evidence`: 8/8 PASS |",
                "| `M03-T01` | `Completed` | "
                "`tests.test_evidence`: 8/8 PASS |",
            ),
            "unknown": ("| `M03-T02` | `Completed`", "| `M03-T99` | `Completed`"),
            "pending": ("| `M03-T02` | `Completed`", "| `M03-T02` | `Pending`"),
        }
        for label, (old, new) in replacements.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(
                        temp_dir,
                        COMPLETE_PLAN.replace(old, new),
                    )

                self.assertTrue(
                    any(
                        issue.code == "EVIDENCE_INCOMPLETE"
                        and "task status" in issue.message
                        for issue in issues
                    )
                )

    def test_traceability_rejects_requirement_and_path_mismatch(self) -> None:
        # Break caught: traceability can claim undeclared requirements or omit files.
        mutations = {
            "unknown requirement": (
                "`REQ-SAMPLE-016` | `src/checks.py`",
                "`REQ-SAMPLE-999` | `src/checks.py`",
            ),
            "missing implementation": (
                "`REQ-SAMPLE-016` | `src/checks.py`",
                "`REQ-SAMPLE-016` | None",
            ),
            "missing tests": (
                "`src/checks.py` | "
                "`tests/test_evidence.py::test_validate`",
                "`src/checks.py` | None",
            ),
        }
        for label, (old, new) in mutations.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(
                        temp_dir,
                        COMPLETE_PLAN.replace(old, new),
                    )

                self.assertTrue(
                    any(issue.code == "EVIDENCE_INCOMPLETE" for issue in issues)
                )

    def test_traceability_requirements_exactly_match_each_task_section(
        self,
    ) -> None:
        # Break caught: globally valid requirements can be swapped or duplicated.
        mutations = {
            "swapped mappings": (
                COMPLETE_PLAN.replace(
                    "| `M03-T01` | `REQ-SAMPLE-010` |",
                    "| `M03-T01` | `REQ-SAMPLE-016` |",
                ).replace(
                    "| `M03-T02` | `REQ-SAMPLE-016` |",
                    "| `M03-T02` | `REQ-SAMPLE-010` |",
                )
            ),
            "omitted mapping": COMPLETE_PLAN.replace(
                "| `M03-T01` | `REQ-SAMPLE-010` |",
                "| `M03-T01` | None |",
            ),
            "duplicated mapping": COMPLETE_PLAN.replace(
                "| `M03-T01` | `REQ-SAMPLE-010` |",
                "| `M03-T01` | `REQ-SAMPLE-010, REQ-SAMPLE-010` |",
            ),
        }
        for label, content in mutations.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(temp_dir, content)

                self.assertTrue(
                    any(
                        issue.code == "EVIDENCE_INCOMPLETE"
                        and "traceability requirements" in issue.message
                        for issue in issues
                    )
                )

    def test_commit_scope_rejects_non_file_paths(self) -> None:
        # Break caught: unsafe path spellings enter the later git allowlist.
        invalid_paths = (
            "../outside.py",
            "/absolute.py",
            r"C:\absolute.py",
            "src/",
            "docs",
            "src/*.py",
            ":(top)README.md",
        )
        for invalid_path in invalid_paths:
            with self.subTest(path=invalid_path):
                content = COMPLETE_PLAN.replace(
                    "`src/evidence.py` | Evidence parser",
                    f"`{invalid_path}` | Evidence parser",
                )
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(temp_dir, content)

                self.assertTrue(
                    any(
                        issue.code == "STAGED_SCOPE_INVALID"
                        and invalid_path in issue.message
                        for issue in issues
                    )
                )

    def test_change_requests_must_exactly_match_approved_change_requests(self) -> None:
        # Break caught: missing or unapproved Change Request IDs enter commit evidence.
        cases = (
            ("- Approved Change Requests: CR-05", "- Approved Change Requests: None"),
            ("- Approved Change Requests: CR-05", "- Approved Change Requests: CR-06"),
            ("- Approved Change Requests: CR-05", "- Approved Change Requests: CR-05, CR-06"),
        )
        for old, new in cases:
            with self.subTest(value=new):
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(
                        temp_dir,
                        COMPLETE_PLAN.replace(old, new),
                    )

                self.assertTrue(
                    any(
                        issue.code == "EVIDENCE_INCOMPLETE"
                        and "approved Change Requests" in issue.message
                        for issue in issues
                    )
                )

    def test_empty_evidence_fields_and_pending_baseline_fail_closed(
        self,
    ) -> None:
        # Break caught: blank metadata and state words masquerade as empty sets.
        cases = (
            (
                "blank Change Requests",
                "- Approved Change Requests: CR-05",
                "- Approved Change Requests:",
                (),
                {"EVIDENCE_INCOMPLETE"},
            ),
            (
                "blank deviations",
                "- Deviations: None",
                "- Deviations:",
                ("CR-05",),
                {"EVIDENCE_INCOMPLETE"},
            ),
            (
                "pending baseline",
                "- Baseline dirty paths: None",
                "- Baseline dirty paths: Pending",
                ("CR-05",),
                {"EVIDENCE_INCOMPLETE", "STAGED_SCOPE_INVALID"},
            ),
            (
                "skipped baseline",
                "- Baseline dirty paths: None",
                "- Baseline dirty paths: Skipped",
                ("CR-05",),
                {"EVIDENCE_INCOMPLETE", "STAGED_SCOPE_INVALID"},
            ),
        )
        for label, old, new, approved, accepted_codes in cases:
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(
                        temp_dir,
                        COMPLETE_PLAN.replace(old, new),
                        approved_change_requests=approved,
                    )

                self.assertTrue(
                    any(issue.code in accepted_codes for issue in issues)
                )

    def test_explicit_none_is_a_valid_empty_evidence_set(self) -> None:
        # Break caught: fail-closed blank handling accidentally rejects explicit None.
        content = COMPLETE_PLAN.replace(
            "- Approved Change Requests: CR-05",
            "- Approved Change Requests: None",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            _, issues = self._parse_and_validate(
                temp_dir,
                content,
                approved_change_requests=(),
            )

        self.assertEqual([], issues)

    def test_none_sentinel_cannot_be_mixed_with_evidence_entries(self) -> None:
        # Break caught: a field claims both an empty set and a concrete entry.
        cases = (
            (
                "Change Requests",
                "- Approved Change Requests: CR-05",
                "- Approved Change Requests: None, CR-05",
                ("CR-05",),
            ),
            (
                "deviations",
                "- Deviations: None",
                "- Deviations: None, DV-01",
                ("CR-05",),
            ),
            (
                "baseline",
                "- Baseline dirty paths: None",
                "- Baseline dirty paths: None, user-notes.md",
                ("CR-05",),
            ),
        )
        for label, old, new, approved in cases:
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(
                        temp_dir,
                        COMPLETE_PLAN.replace(old, new),
                        approved_change_requests=approved,
                    )

                evidence_issues = [
                    issue
                    for issue in issues
                    if issue.code == "EVIDENCE_INCOMPLETE"
                ]
                self.assertEqual(1, len(evidence_issues))

    def test_completed_task_rejects_failed_actual_verification(self) -> None:
        # Break caught: Completed status accepts an explicit task-level failure.
        for failure_word in ("FAIL", "fail"):
            with self.subTest(actual=failure_word):
                content = COMPLETE_PLAN.replace(
                    "`tests.test_evidence`: 8/8 PASS",
                    failure_word,
                    1,
                )
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(temp_dir, content)

                self.assertTrue(
                    any(
                        issue.code == "EVIDENCE_INCOMPLETE"
                        and "actual verification" in issue.message
                        for issue in issues
                    )
                )

    def test_completed_task_requires_affirmative_pass_evidence(self) -> None:
        # Break caught: absence of FAIL is mistaken for affirmative test success.
        rejected = (
            "ERROR",
            "not run due to timeout",
            "Pending",
            "Skipped",
            "",
        )
        for actual in rejected:
            with self.subTest(actual=actual):
                content = COMPLETE_PLAN.replace(
                    "`tests.test_evidence`: 8/8 PASS",
                    actual,
                    1,
                )
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(temp_dir, content)

                self.assertTrue(
                    any(
                        issue.code == "EVIDENCE_INCOMPLETE"
                        and "actual verification" in issue.message
                        for issue in issues
                    )
                )

    def test_completed_task_accepts_standalone_pass_or_passed(self) -> None:
        # Break caught: affirmative success matching becomes case-sensitive or exact.
        accepted = ("8/8 PASS", "43/43 passed")
        for actual in accepted:
            with self.subTest(actual=actual):
                content = COMPLETE_PLAN.replace(
                    "`tests.test_evidence`: 8/8 PASS",
                    actual,
                    1,
                )
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(temp_dir, content)

                self.assertFalse(
                    any(
                        issue.code == "EVIDENCE_INCOMPLETE"
                        and "actual verification" in issue.message
                        for issue in issues
                    )
                )

    def test_verification_requires_targeted_and_broader_pass(self) -> None:
        # Break caught: missing or non-passing verification is treated as delivery-ready.
        targeted = (
            "| Targeted | `python -m unittest tests.test_evidence -v` | "
            "All pass | 8/8 pass | PASS |\n"
        )
        broader = (
            "| Broader | `python -m unittest discover -s tests -v` | "
            "All pass | 70/70 pass | PASS |\n"
        )
        cases = {
            "missing targeted": (targeted, ""),
            "missing broader": (broader, ""),
            "failed": ("| PASS |\n\n### Commit scope", "| FAIL |\n\n### Commit scope"),
            "pending actual": ("| 8/8 pass | PASS |", "| Pending | PASS |"),
            "empty command": (
                "`python -m unittest tests.test_evidence -v`",
                "None",
            ),
        }
        for label, (old, new) in cases.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(
                        temp_dir,
                        COMPLETE_PLAN.replace(old, new, 1),
                    )

                self.assertTrue(
                    any(
                        issue.code == "VERIFICATION_NOT_PASSED"
                        for issue in issues
                    )
                )

    def test_verification_actual_must_affirm_success_even_when_result_is_pass(
        self,
    ) -> None:
        # Break caught: a PASS result overrides contradictory or unperformed Actual.
        for actual in (
            "1/8 failed",
            "ERROR",
            "not run",
            "not run due to timeout",
        ):
            with self.subTest(actual=actual):
                content = COMPLETE_PLAN.replace(
                    "| 8/8 pass | PASS |",
                    f"| {actual} | PASS |",
                    1,
                )
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(temp_dir, content)

                verification_issues = [
                    issue
                    for issue in issues
                    if issue.code == "VERIFICATION_NOT_PASSED"
                ]
                self.assertTrue(verification_issues)
                self.assertTrue(
                    any("Targeted" in issue.message for issue in verification_issues)
                )

    def test_verification_actual_accepts_standalone_pass_or_passed(
        self,
    ) -> None:
        # Break caught: shared affirmative matching rejects canonical result counts.
        for actual in ("8/8 PASS", "43/43 passed"):
            with self.subTest(actual=actual):
                content = COMPLETE_PLAN.replace(
                    "| 8/8 pass | PASS |",
                    f"| {actual} | PASS |",
                    1,
                )
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(temp_dir, content)

                self.assertFalse(
                    any(
                        issue.code == "VERIFICATION_NOT_PASSED"
                        for issue in issues
                    )
                )

    def test_fenced_examples_do_not_supply_evidence(self) -> None:
        # Break caught: canonical-looking example tables are parsed as real evidence.
        prefix, tail = COMPLETE_PLAN.split("## Traceability", 1)
        hidden_body = (
            "## Traceability"
            + tail.split("### Commit draft", 1)[0]
        )
        visible_draft = """\
## Evidence and commit

### Commit draft

```text
feat(evidence): validate milestone evidence
```
"""
        for marker in ("```", "~~~"):
            with self.subTest(marker=marker):
                content = (
                    prefix
                    + "## Examples\n\n"
                    + marker
                    + "text\n"
                    + hidden_body
                    + marker
                    + "\n\n"
                    + visible_draft
                )
                with tempfile.TemporaryDirectory() as temp_dir:
                    repo_root, plan_path = self._write_plan(temp_dir, content)
                    record = parse_evidence(repo_root, plan_path)

                self.assertEqual(0, record.traceability_table_count)
                self.assertEqual(0, record.task_status_table_count)
                self.assertEqual(0, record.verification_table_count)
                self.assertEqual(0, record.commit_scope_table_count)
                self.assertEqual(0, record.approved_change_requests_count)
                self.assertEqual(0, record.deviations_count)
                self.assertEqual(0, record.baseline_dirty_paths_count)
                self.assertEqual(1, record.commit_draft_count)

    def test_html_comments_do_not_supply_evidence_but_visible_content_does(
        self,
    ) -> None:
        # Break caught: multiline HTML comments duplicate otherwise valid evidence.
        prefix, tail = COMPLETE_PLAN.split("## Traceability", 1)
        hidden_body = (
            "## Traceability"
            + tail.split("### Commit draft", 1)[0]
        )
        content = prefix + "<!--\n" + hidden_body + "-->\n\n## Traceability" + tail
        with tempfile.TemporaryDirectory() as temp_dir:
            record, issues = self._parse_and_validate(temp_dir, content)

        self.assertEqual(1, record.traceability_table_count)
        self.assertEqual(1, record.task_status_table_count)
        self.assertEqual(1, record.verification_table_count)
        self.assertEqual(1, record.commit_scope_table_count)
        self.assertEqual(
            ("M03-T01", "M03-T02"),
            tuple(row.task_id for row in record.traceability),
        )
        self.assertEqual([], issues)

    def test_contradictory_success_text_fails_closed(self) -> None:
        # Break caught: a PASS/PASSED token hides zero success or nonzero return.
        for actual in ("0/8 passed", "PASS; command returned 1"):
            with self.subTest(location="task status", actual=actual):
                content = COMPLETE_PLAN.replace(
                    "`tests.test_evidence`: 8/8 PASS",
                    actual,
                    1,
                )
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(temp_dir, content)
                self.assertTrue(
                    any(
                        issue.code == "EVIDENCE_INCOMPLETE"
                        and "actual verification" in issue.message
                        for issue in issues
                    )
                )

            with self.subTest(location="verification", actual=actual):
                content = COMPLETE_PLAN.replace(
                    "| 8/8 pass | PASS |",
                    f"| {actual} | PASS |",
                    1,
                )
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(temp_dir, content)
                self.assertTrue(
                    any(
                        issue.code == "VERIFICATION_NOT_PASSED"
                        for issue in issues
                    )
                )

    def test_documented_success_forms_remain_valid(self) -> None:
        # Break caught: the narrow success grammar rejects an approved canonical form.
        for actual in (
            "PASS",
            "tests.test_example: PASS",
            "8/8 PASS",
            "43/43 passed",
        ):
            with self.subTest(actual=actual):
                content = COMPLETE_PLAN.replace(
                    "`tests.test_evidence`: 8/8 PASS",
                    actual,
                    1,
                ).replace(
                    "| 8/8 pass | PASS |",
                    f"| {actual} | PASS |",
                    1,
                )
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(temp_dir, content)

                self.assertEqual([], issues)

    def test_indented_code_block_tables_do_not_supply_evidence(self) -> None:
        # Break caught: CommonMark indented code is mistaken for live table syntax.
        for indent in ("    ", "\t"):
            with self.subTest(indent=repr(indent)):
                content = "\n".join(
                    indent + line if line.startswith("|") else line
                    for line in COMPLETE_PLAN.splitlines()
                )
                with tempfile.TemporaryDirectory() as temp_dir:
                    repo_root, plan_path = self._write_plan(temp_dir, content)
                    record = parse_evidence(repo_root, plan_path)

                self.assertEqual(0, record.traceability_table_count)
                self.assertEqual(0, record.task_status_table_count)
                self.assertEqual(0, record.verification_table_count)
                self.assertEqual(0, record.commit_scope_table_count)

    def test_tables_with_three_leading_spaces_remain_canonical(self) -> None:
        # Break caught: the code-block guard rejects legal non-code indentation.
        content = "\n".join(
            "   " + line if line.startswith("|") else line
            for line in COMPLETE_PLAN.splitlines()
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            _, issues = self._parse_and_validate(temp_dir, content)

        self.assertEqual([], issues)

    def test_commit_draft_requires_matching_closing_fence(self) -> None:
        # Break caught: EOF, another marker, or a short marker closes the draft.
        without_close, _, _ = COMPLETE_PLAN.rpartition("```")
        cases = (
            ("eof", without_close),
            ("different marker", without_close + "~~~\n"),
            (
                "short closing",
                COMPLETE_PLAN.replace(
                    "```text\nfeat(evidence)",
                    "````text\nfeat(evidence)",
                    1,
                ),
            ),
        )
        for label, content in cases:
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(temp_dir, content)

                self.assertTrue(
                    any(
                        issue.code == "EVIDENCE_INCOMPLETE"
                        and "commit draft" in issue.message
                        for issue in issues
                    )
                )

    def test_commit_draft_fence_rejects_code_block_indentation(self) -> None:
        # Break caught: an indented code block is treated as a Markdown fence.
        for indent in ("    ", "\t"):
            with self.subTest(indent=repr(indent)):
                content = COMPLETE_PLAN.replace(
                    "```text\nfeat(evidence)",
                    indent + "```text\nfeat(evidence)",
                    1,
                )
                before_close, marker, after_close = content.rpartition("```")
                content = before_close + indent + marker + after_close
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(temp_dir, content)

                self.assertTrue(
                    any(
                        issue.code == "EVIDENCE_INCOMPLETE"
                        and "commit draft" in issue.message
                        for issue in issues
                    )
                )

    def test_commit_draft_fence_accepts_up_to_three_spaces(self) -> None:
        # Break caught: the CommonMark indentation guard rejects a legal fence.
        for indent in ("", " ", "   "):
            with self.subTest(indent=repr(indent)):
                content = COMPLETE_PLAN.replace(
                    "```text\nfeat(evidence)",
                    indent + "```text\nfeat(evidence)",
                    1,
                )
                before_close, marker, after_close = content.rpartition("```")
                content = before_close + indent + marker + after_close
                with tempfile.TemporaryDirectory() as temp_dir:
                    _, issues = self._parse_and_validate(temp_dir, content)

                self.assertEqual([], issues)

    def test_arbitrary_prose_and_tables_do_not_supply_evidence(self) -> None:
        # Break caught: parser guesses rows from a similarly shaped appendix table.
        content = COMPLETE_PLAN.replace(
            "## Traceability",
            "## Notes\n\n"
            "| Task | Requirements | Implementation | Tests |\n"
            "|---|---|---|---|\n"
            "| `M03-T99` | `REQ-SAMPLE-999` | `bad.py` | `bad.py` |\n\n"
            "## Traceability",
        ).replace(
            "| `M03-T01` | `REQ-SAMPLE-010` | `src/evidence.py` | "
            "`tests/test_evidence.py::test_parse` |\n"
            "| `M03-T02` | `REQ-SAMPLE-016` | `src/checks.py` | "
            "`tests/test_evidence.py::test_validate` |\n",
            "",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            record, issues = self._parse_and_validate(temp_dir, content)

        self.assertEqual((), record.traceability)
        self.assertTrue(
            any(
                issue.code == "EVIDENCE_INCOMPLETE"
                and "traceability task" in issue.message
                for issue in issues
            )
        )

    def test_issues_are_stably_sorted_by_path_line_and_code(self) -> None:
        # Break caught: validation branch order leaks into public issue ordering.
        content = (
            COMPLETE_PLAN.replace(
                "| `M03-T02` | `Completed`",
                "| `M03-T02` | `Pending`",
            )
            .replace(
                "| Targeted | `python -m unittest tests.test_evidence -v` | "
                "All pass | 8/8 pass | PASS |\n",
                "",
            )
            .replace(
                "`src/evidence.py` | Evidence parser",
                "`../outside.py` | Evidence parser",
            )
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            _, issues = self._parse_and_validate(temp_dir, content)

        keys = [
            (issue.path.as_posix().casefold(), issue.line, issue.code)
            for issue in issues
        ]
        self.assertGreaterEqual(len(keys), 3)
        self.assertEqual(sorted(keys), keys)


if __name__ == "__main__":
    unittest.main()
