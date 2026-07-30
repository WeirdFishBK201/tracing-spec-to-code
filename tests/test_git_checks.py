from __future__ import annotations

import dataclasses
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "tracing-spec-to-code" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from tstc.evidence import parse_evidence
import tstc.git_checks as git_checks_module
from tstc.git_checks import (
    GitInspectionError,
    get_staged_paths,
    validate_commit_message,
    validate_staged_scope,
)
from tstc.precommit import PrecommitRuntimeError, validate_precommit
from tstc.validation import validate_repository


PLAN_RELATIVE = Path("docs/plans/sample-m01-contracts.md")
SCOPE = (
    PLAN_RELATIVE,
    Path("docs/plans/sample-roadmap.md"),
    Path("docs/changes/sample-cp01-traceability.md"),
    Path("src/app.py"),
    Path("tests/test_app.py"),
)
CUSTOM_PROPOSAL_TEMPLATE = (
    "{feature}-change-{proposal}-{proposal_slug}.md"
)
CUSTOM_CP01 = Path("docs/changes/sample-change-01-traceability.md")
PLAN = """\
# Sample M01 Contracts Plan

- Status: Approved — In Progress
- Milestone: M01 — Contracts
- Requirements: REQ-SAMPLE-001, REQ-SAMPLE-002
- Gate P: Approved

## Tasks

### M01-T01 — Discover artifacts

- Requirements: REQ-SAMPLE-001

### M01-T02 — Check traceability

- Requirements: REQ-SAMPLE-002

## Traceability

| Task | Requirements | Implementation | Tests |
|---|---|---|---|
| `M01-T01` | `REQ-SAMPLE-001` | `src/app.py` | `tests/test_app.py::test_discover` |
| `M01-T02` | `REQ-SAMPLE-002` | `src/app.py` | `tests/test_app.py::test_traceability` |

## Evidence and commit

### Task status

| Task | Status | Actual verification |
|---|---|---|
| `M01-T01` | `Completed` | `tests.test_app`: 2/2 PASS |
| `M01-T02` | `Completed` | `tests.test_app`: 2/2 PASS |

- Approved proposals: CP-01
- Deviations: None
- Baseline dirty paths: None

### Verification

| Scope | Command | Expected | Actual | Result |
|---|---|---|---|---|
| Targeted | `python -m unittest tests.test_app` | All pass | 2/2 PASS | PASS |
| Broader | `python -m unittest discover -s tests` | All pass | 2/2 PASS | PASS |

### Commit scope

| Path | Purpose |
|---|---|
| `docs/plans/sample-m01-contracts.md` | Milestone evidence |
| `docs/plans/sample-roadmap.md` | Milestone status |
| `docs/changes/sample-cp01-traceability.md` | Approved proposal |
| `src/app.py` | Implementation |
| `tests/test_app.py` | Behavior tests |

### Commit draft

```text
feat(evidence): validate milestone delivery

Milestone: M01 Contracts
Requirements: REQ-SAMPLE-001, REQ-SAMPLE-002
Change-Proposals: CP-01
```
"""


def git(repo_root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *arguments],
        capture_output=True,
        check=False,
    )


def require_git(repo_root: Path, *arguments: str) -> bytes:
    result = git(repo_root, *arguments)
    if result.returncode:
        raise AssertionError(result.stderr.decode(errors="replace"))
    return result.stdout


def prepare_repository(
    temp_dir: str,
    *,
    initialize_git: bool = True,
    custom_proposal_template: bool = False,
) -> Path:
    repo_root = Path(temp_dir).resolve() / "sample"
    shutil.copytree(REPO_ROOT / "tests/fixtures/valid-project", repo_root)
    plan_content = PLAN
    scope = SCOPE
    if custom_proposal_template:
        default_proposal = Path(
            "docs/changes/sample-cp01-traceability.md"
        )
        (repo_root / default_proposal).rename(repo_root / CUSTOM_CP01)
        config_path = repo_root / ".tracing-spec-to-code.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["change_proposal_filename_template"] = (
            CUSTOM_PROPOSAL_TEMPLATE
        )
        config_path.write_text(
            json.dumps(config, indent=2) + "\n",
            encoding="utf-8",
        )
        plan_content = plan_content.replace(
            default_proposal.as_posix(),
            CUSTOM_CP01.as_posix(),
        )
        scope = tuple(
            CUSTOM_CP01 if path == default_proposal else path
            for path in scope
        )
    (repo_root / PLAN_RELATIVE).write_text(plan_content, encoding="utf-8")
    (repo_root / "src").mkdir()
    (repo_root / "src/app.py").write_text("VALUE = 0\n", encoding="utf-8")
    (repo_root / "tests").mkdir()
    (repo_root / "tests/test_app.py").write_text(
        "def test_placeholder():\n    assert True\n",
        encoding="utf-8",
    )
    (repo_root / "user-notes.txt").write_text("original\n", encoding="utf-8")
    if not initialize_git:
        return repo_root

    require_git(repo_root, "init", "-q")
    require_git(repo_root, "config", "user.name", "Test User")
    require_git(repo_root, "config", "user.email", "test@example.com")
    require_git(repo_root, "config", "core.autocrlf", "false")
    require_git(repo_root, "add", "--", ".")
    require_git(repo_root, "commit", "-q", "-m", "test: baseline")

    for relative in scope[:3]:
        path = repo_root / relative
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    (repo_root / "src/app.py").write_text("VALUE = 1\n", encoding="utf-8")
    (repo_root / "tests/test_app.py").write_text(
        "def test_discover():\n    assert True\n\n"
        "def test_traceability():\n    assert True\n",
        encoding="utf-8",
    )
    require_git(repo_root, "add", "--", *(path.as_posix() for path in scope))
    (repo_root / "user-notes.txt").write_text(
        "original\nprivate change\n",
        encoding="utf-8",
    )
    return repo_root


def git_snapshot(repo_root: Path) -> tuple[bytes, ...]:
    return (
        require_git(repo_root, "rev-parse", "HEAD"),
        require_git(repo_root, "status", "--porcelain=v1", "-z"),
        require_git(repo_root, "diff", "--cached", "--binary"),
        require_git(repo_root, "diff", "--binary"),
        require_git(repo_root, "remote", "-v"),
    )


def write_proposal(
    repo_root: Path,
    *,
    proposal_id: str,
    task_id: str,
    status: str = "Approved",
    gate: str = "Approved",
    filename: str | None = None,
    affected_label: str = "Affected tasks",
    affected_separator: str = ":",
    top_extra: str = "",
    impact: str = "No interface change.",
) -> Path:
    number = int(proposal_id.split("-", 1)[1])
    path = (
        repo_root
        / "docs"
        / "changes"
        / (filename or f"sample-cp{number:02d}-additional.md")
    )
    path.write_text(
        f"""\
# {proposal_id} — Additional context

- Status: {status}
- Gate Δ: {gate}
- Requirements: REQ-SAMPLE-001
- {affected_label}{affected_separator} {task_id}
{top_extra}

## Proposed delta

Clarify one workflow edge.

## Impact

{impact}
""",
        encoding="utf-8",
    )
    return path


class GitChecksTests(unittest.TestCase):
    def test_exact_staged_set_and_commit_draft_are_valid(self) -> None:
        # Break caught: valid Git state is rejected or read using lossy text splitting.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            record = parse_evidence(repo_root, repo_root / PLAN_RELATIVE)

            staged = get_staged_paths(repo_root)
            scope_issues = validate_staged_scope(record, staged)
            message_issues = validate_commit_message(record)

        self.assertEqual(
            tuple(sorted(SCOPE, key=lambda path: path.as_posix().casefold())),
            staged,
        )
        self.assertEqual([], scope_issues)
        self.assertEqual([], message_issues)

    def test_extra_and_missing_staged_paths_fail_exact_set_equality(self) -> None:
        # Break caught: subset checks allow unrelated files or omit promised files.
        for label in ("extra", "missing"):
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as temp_dir:
                    repo_root = prepare_repository(temp_dir)
                    if label == "extra":
                        require_git(repo_root, "add", "--", "user-notes.txt")
                    else:
                        require_git(
                            repo_root,
                            "restore",
                            "--staged",
                            "--",
                            "src/app.py",
                        )
                    record = parse_evidence(repo_root, repo_root / PLAN_RELATIVE)

                    issues = validate_staged_scope(
                        record,
                        get_staged_paths(repo_root),
                    )

                self.assertTrue(
                    any(issue.code == "STAGED_SCOPE_INVALID" for issue in issues)
                )

    def test_baseline_overlap_and_invalid_scope_fail_closed(self) -> None:
        # Break caught: pre-existing user edits can be silently mixed into a commit.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            plan_path = repo_root / PLAN_RELATIVE
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8").replace(
                    "- Baseline dirty paths: None",
                    "- Baseline dirty paths: src/app.py",
                ),
                encoding="utf-8",
            )
            record = parse_evidence(repo_root, plan_path)
            overlap = validate_staged_scope(record, get_staged_paths(repo_root))
            invalid_sets = {
                invalid_path: validate_staged_scope(
                    dataclasses.replace(
                        record,
                        commit_scope=(
                            dataclasses.replace(
                                record.commit_scope[0],
                                path=invalid_path,
                            ),
                        ),
                    ),
                    (),
                )
                for invalid_path in ("../escape", ":(top)README.md")
            }

        self.assertTrue(
            any(
                issue.code == "STAGED_SCOPE_INVALID"
                and "baseline" in issue.message
                for issue in overlap
            )
        )
        self.assertTrue(
            all(
                any(
                    issue.code == "STAGED_SCOPE_INVALID"
                    and "invalid" in issue.message
                    for issue in issues
                )
                for issues in invalid_sets.values()
            )
        )
        self.assertTrue(
            any(
                "pathspec magic" in issue.message
                for issue in invalid_sets[":(top)README.md"]
            )
        )

    def test_path_identity_obeys_case_insensitive_filesystem_semantics(
        self,
    ) -> None:
        # Break caught: case variants evade overlap, equality, or duplicate checks.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            record = parse_evidence(repo_root, repo_root / PLAN_RELATIVE)
            case_baseline = dataclasses.replace(
                record,
                baseline_dirty_paths=("SRC/APP.PY",),
            )
            staged = tuple(
                Path("SRC/APP.PY") if path == Path("src/app.py") else path
                for path in get_staged_paths(repo_root)
            )
            duplicate = dataclasses.replace(
                record,
                commit_scope=record.commit_scope
                + (
                    dataclasses.replace(
                        next(
                            row
                            for row in record.commit_scope
                            if row.path == "src/app.py"
                        ),
                        path="SRC/APP.PY",
                    ),
                ),
            )

            with mock.patch.object(
                git_checks_module,
                "_CASE_INSENSITIVE_PATHS",
                True,
                create=True,
            ):
                insensitive = validate_staged_scope(case_baseline, staged)
                duplicate_issues = validate_staged_scope(duplicate, staged)
            with mock.patch.object(
                git_checks_module,
                "_CASE_INSENSITIVE_PATHS",
                False,
                create=True,
            ):
                sensitive = validate_staged_scope(case_baseline, staged)

        self.assertTrue(
            any("baseline" in issue.message for issue in insensitive)
        )
        self.assertFalse(
            any("not staged" in issue.message for issue in insensitive)
        )
        self.assertFalse(
            any("outside commit scope" in issue.message for issue in insensitive)
        )
        self.assertTrue(
            any("duplicate commit scope" in issue.message for issue in duplicate_issues)
        )
        self.assertFalse(any("baseline" in issue.message for issue in sensitive))
        self.assertTrue(any("not staged" in issue.message for issue in sensitive))
        self.assertTrue(
            any("outside commit scope" in issue.message for issue in sensitive)
        )

    def test_duplicate_scope_and_unormalized_staged_path_fail_closed(self) -> None:
        # Break caught: duplicate or non-canonical path spellings bypass set comparison.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            record = parse_evidence(repo_root, repo_root / PLAN_RELATIVE)
            duplicate = dataclasses.replace(
                record,
                commit_scope=(record.commit_scope[0], record.commit_scope[0]),
            )

            duplicate_issues = validate_staged_scope(
                duplicate,
                (PLAN_RELATIVE,),
            )
            staged_issues = validate_staged_scope(
                record,
                (Path("../escape"),),
            )

        self.assertTrue(
            any("duplicate" in issue.message for issue in duplicate_issues)
        )
        self.assertTrue(
            any(
                "invalid staged path" in issue.message
                for issue in staged_issues
            )
        )

    def test_commit_message_requires_exact_subject_and_trailers(self) -> None:
        # Break caught: malformed, duplicated, unknown, or mismatched trailers pass.
        invalid_messages = (
            "update files\n\nMilestone: M01 Contracts\n"
            "Requirements: REQ-SAMPLE-001, REQ-SAMPLE-002\n"
            "Change-Proposals: CP-01",
            "feat(evidence): validate milestone delivery\n\n"
            "Milestone: M02 Other\n"
            "Requirements: REQ-SAMPLE-001, REQ-SAMPLE-002\n"
            "Change-Proposals: CP-01",
            "feat(evidence): validate milestone delivery\n\n"
            "Milestone: M01 Contracts\nMilestone: M01 Contracts\n"
            "Requirements: REQ-SAMPLE-001, REQ-SAMPLE-002\n"
            "Change-Proposals: CP-01",
            "feat(evidence): validate milestone delivery\n\n"
            "Milestone: M01 Contracts\n"
            "Requirements: REQ-SAMPLE-002, REQ-SAMPLE-001\n"
            "Change-Proposals: CP-01",
            "feat(evidence): validate milestone delivery\n\n"
            "Milestone: M01 Contracts\n"
            "Requirements: REQ-SAMPLE-001, REQ-SAMPLE-002\n"
            "Change-Proposals: CP-99",
            "feat(evidence): validate milestone delivery\n\n"
            "Milestone: M01 Contracts\n"
            "Requirements: REQ-SAMPLE-001, REQ-SAMPLE-002\n"
            "Change-Proposals CP-01",
            "feat(evidence): validate milestone delivery\n\n"
            "Milestone: M01 Contracts\n"
            "Requirements: REQ-SAMPLE-001, REQ-SAMPLE-002\n"
            "Unknown-Trailer: value",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            record = parse_evidence(repo_root, repo_root / PLAN_RELATIVE)
            issue_sets = [
                validate_commit_message(
                    dataclasses.replace(record, commit_message=message)
                )
                for message in invalid_messages
            ]

        self.assertTrue(
            all(
                any(issue.code == "COMMIT_MESSAGE_INVALID" for issue in issues)
                for issues in issue_sets
            )
        )

    def test_change_proposals_trailer_is_forbidden_for_empty_set(self) -> None:
        # Break caught: proposal trailers can claim approvals not in evidence.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            record = parse_evidence(repo_root, repo_root / PLAN_RELATIVE)
            without_proposals = dataclasses.replace(
                record,
                approved_proposals=(),
            )

            issues = validate_commit_message(without_proposals)

        self.assertTrue(
            any(issue.code == "COMMIT_MESSAGE_INVALID" for issue in issues)
        )

    def test_non_git_repository_raises_narrow_runtime_error(self) -> None:
        # Break caught: Git invocation failure is guessed as an empty staged set.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir, initialize_git=False)

            with self.assertRaises(GitInspectionError):
                get_staged_paths(repo_root)
            with self.assertRaises(PrecommitRuntimeError):
                validate_precommit(repo_root, repo_root / PLAN_RELATIVE)

    def test_staged_rename_reports_both_affected_paths(self) -> None:
        # Break caught: rename detection hides deletion of an out-of-scope path.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            require_git(
                repo_root,
                "mv",
                "user-notes.txt",
                "moved-notes.txt",
            )

            staged = {path.as_posix() for path in get_staged_paths(repo_root)}

        self.assertIn("user-notes.txt", staged)
        self.assertIn("moved-notes.txt", staged)

    def test_precommit_rejects_non_discovered_or_outside_plan(self) -> None:
        # Break caught: a historical or external plan can be selected by path alone.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            other = repo_root / "notes.md"
            other.write_text(PLAN, encoding="utf-8")
            outside = Path(temp_dir) / "outside.md"
            outside.write_text(PLAN, encoding="utf-8")

            for plan_path in (other, outside):
                with self.subTest(path=plan_path):
                    with self.assertRaises(PrecommitRuntimeError):
                        validate_precommit(repo_root, plan_path)

    def test_precommit_rejects_discovered_historical_plan_selection(self) -> None:
        # Break caught: exact discovery alone permits committing a past milestone.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            plan_path = repo_root / PLAN_RELATIVE
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8").replace(
                    "- Status: Approved — In Progress",
                    "- Status: Completed",
                ),
                encoding="utf-8",
            )
            roadmap_path = repo_root / "docs/plans/sample-roadmap.md"
            roadmap = (
                roadmap_path.read_text(encoding="utf-8")
                .replace("- Status: Approved", "- Status: Awaiting")
                .replace(
                    "- Current milestone: M01",
                    "- Current milestone: M02",
                )
                + "| M02 — Next | Await planning | REQ-SAMPLE-001 | "
                "M01 | Handoff |\n"
            )
            roadmap_path.write_text(roadmap, encoding="utf-8")
            require_git(
                repo_root,
                "add",
                "--",
                PLAN_RELATIVE.as_posix(),
                "docs/plans/sample-roadmap.md",
            )
            before = git_snapshot(repo_root)

            with self.assertRaisesRegex(
                PrecommitRuntimeError,
                "roadmap current milestone",
            ):
                validate_precommit(repo_root, plan_path)

            after = git_snapshot(repo_root)

        self.assertEqual(before, after)

    def test_precommit_requires_plan_roadmap_and_approved_proposal_in_scope(
        self,
    ) -> None:
        # Break caught: an exact staged set omits milestone governance artifacts.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            plan_path = repo_root / PLAN_RELATIVE
            content = plan_path.read_text(encoding="utf-8")
            content = content.replace(
                "| `docs/plans/sample-roadmap.md` | Milestone status |\n",
                "",
            ).replace(
                "| `docs/changes/sample-cp01-traceability.md` | "
                "Approved proposal |\n",
                "",
            )
            plan_path.write_text(content, encoding="utf-8")
            require_git(repo_root, "add", "--", PLAN_RELATIVE.as_posix())
            require_git(
                repo_root,
                "restore",
                "--staged",
                "--",
                "docs/plans/sample-roadmap.md",
                "docs/changes/sample-cp01-traceability.md",
            )

            issues = validate_precommit(repo_root, plan_path)

        missing = {
            path
            for issue in issues
            if issue.code == "STAGED_SCOPE_INVALID"
            for path in (
                "docs/plans/sample-roadmap.md",
                "docs/changes/sample-cp01-traceability.md",
            )
            if path in issue.message
        }
        self.assertEqual(
            {
                "docs/plans/sample-roadmap.md",
                "docs/changes/sample-cp01-traceability.md",
            },
            missing,
        )

    def test_precommit_rejects_unstaged_content_in_any_scoped_path(self) -> None:
        # Break caught: validation reads valid worktree content while committing
        # a stale or invalid staged version of the same scoped file.
        cases = (
            (PLAN_RELATIVE, "invalid staged plan"),
            (Path("src/app.py"), "VALUE = 2\n"),
        )
        for relative, worktree_content in cases:
            with self.subTest(path=relative.as_posix()):
                with tempfile.TemporaryDirectory() as temp_dir:
                    repo_root = prepare_repository(temp_dir)
                    target = repo_root / relative
                    if relative == PLAN_RELATIVE:
                        valid_plan = target.read_text(encoding="utf-8")
                        target.write_text(
                            valid_plan.replace(
                                "feat(evidence): validate milestone delivery",
                                "invalid staged subject",
                            ),
                            encoding="utf-8",
                        )
                        require_git(
                            repo_root,
                            "add",
                            "--",
                            relative.as_posix(),
                        )
                        target.write_text(valid_plan, encoding="utf-8")
                    else:
                        target.write_text(worktree_content, encoding="utf-8")
                    before = git_snapshot(repo_root)

                    issues = validate_precommit(repo_root, repo_root / PLAN_RELATIVE)

                    after = git_snapshot(repo_root)

                self.assertTrue(
                    any(
                        issue.code == "STAGED_SCOPE_INVALID"
                        and relative.as_posix() in issue.message
                        and "unstaged" in issue.message
                        for issue in issues
                    )
                )
                self.assertEqual(before, after)

    def test_precommit_rejects_staged_deletion_when_path_reappears(
        self,
    ) -> None:
        # Break caught: index deletion passes while validation reads recreated content.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            require_git(
                repo_root,
                "rm",
                "--cached",
                "-f",
                "--",
                "src/app.py",
            )
            (repo_root / "unrelated.tmp").write_text(
                "leave me alone\n",
                encoding="utf-8",
            )
            before = git_snapshot(repo_root)

            issues = validate_precommit(repo_root, repo_root / PLAN_RELATIVE)

            after = git_snapshot(repo_root)

        self.assertTrue(
            any(
                issue.code == "STAGED_SCOPE_INVALID"
                and "src/app.py" in issue.message
                and "deletion" in issue.message
                for issue in issues
            )
        )
        self.assertEqual(before, after)

    def test_precommit_requires_traceability_files_in_commit_scope(self) -> None:
        # Break caught: claimed implementation/tests evidence is omitted from commit.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            plan_path = repo_root / PLAN_RELATIVE
            content = plan_path.read_text(encoding="utf-8").replace(
                "| `src/app.py` | Implementation |\n",
                "",
            ).replace(
                "| `tests/test_app.py` | Behavior tests |\n",
                "",
            )
            plan_path.write_text(content, encoding="utf-8")
            require_git(repo_root, "add", "--", PLAN_RELATIVE.as_posix())
            require_git(
                repo_root,
                "restore",
                "--staged",
                "--",
                "src/app.py",
                "tests/test_app.py",
            )

            issues = validate_precommit(repo_root, plan_path)

        required_messages = [
            issue.message
            for issue in issues
            if issue.code == "STAGED_SCOPE_INVALID"
            and "required milestone artifact" in issue.message
        ]
        self.assertEqual(1, sum("src/app.py" in value for value in required_messages))
        self.assertEqual(
            1,
            sum("tests/test_app.py" in value for value in required_messages),
        )

    def test_precommit_ignores_approved_historical_task_proposal(self) -> None:
        # Break caught: every repository approval is treated as current milestone scope.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            historical = write_proposal(
                repo_root,
                proposal_id="CP-02",
                task_id="M00-T01",
            )
            before = git_snapshot(repo_root)

            issues = validate_precommit(repo_root, repo_root / PLAN_RELATIVE)

            after = git_snapshot(repo_root)
            staged = {
                path.as_posix()
                for path in get_staged_paths(repo_root)
            }

        self.assertEqual([], issues)
        self.assertEqual(before, after)
        self.assertNotIn(
            historical.relative_to(repo_root).as_posix(),
            staged,
        )

    def test_proposal_ownership_ignores_comments_fences_and_prose(self) -> None:
        # Break caught: incidental task text is mistaken for structured ownership.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            write_proposal(
                repo_root,
                proposal_id="CP-02",
                task_id="M00-T01",
                top_extra=(
                    "<!-- - Affected tasks: M01-T01 -->\n"
                    "```text\n"
                    "- Affected tasks: M01-T01\n"
                    "```"
                ),
                impact="This example mentions M01-T01 but does not affect it.",
            )

            issues = validate_precommit(repo_root, repo_root / PLAN_RELATIVE)

        self.assertEqual([], issues)

    def test_chinese_affected_task_metadata_selects_current_proposal(self) -> None:
        # Break caught: repository-native Chinese metadata is silently ignored.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            current = write_proposal(
                repo_root,
                proposal_id="CP-02",
                task_id="M00-T01， M01-T01",
                affected_label="影响 Task",
                affected_separator="：",
            )

            issues = validate_precommit(repo_root, repo_root / PLAN_RELATIVE)

        current_path = current.relative_to(repo_root).as_posix()
        self.assertTrue(
            any(
                issue.code == "EVIDENCE_INCOMPLETE"
                and "approved proposals" in issue.message
                for issue in issues
            )
        )
        self.assertTrue(
            any(
                issue.code == "STAGED_SCOPE_INVALID"
                and current_path in issue.message
                for issue in issues
            )
        )

    def test_approved_proposal_invalid_affected_task_metadata_fails_closed(
        self,
    ) -> None:
        # Break caught: ambiguous ownership is treated as a historical proposal.
        mutations = {
            "missing": lambda content: content.replace(
                "- Affected tasks: M01-T01\n",
                "",
            ),
            "duplicate": lambda content: content.replace(
                "- Affected tasks: M01-T01\n",
                "- Affected tasks: M01-T01\n"
                "- Affected tasks: M01-T02\n",
            ),
            "empty": lambda content: content.replace(
                "- Affected tasks: M01-T01",
                "- Affected tasks:",
            ),
            "invalid": lambda content: content.replace(
                "- Affected tasks: M01-T01",
                "- Affected tasks: M1-T1",
            ),
            "duplicate value": lambda content: content.replace(
                "- Affected tasks: M01-T01",
                "- Affected tasks: M01-T01, M01-T01",
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as temp_dir:
                    repo_root = prepare_repository(temp_dir)
                    proposal = write_proposal(
                        repo_root,
                        proposal_id="CP-02",
                        task_id="M01-T01",
                    )
                    proposal.write_text(
                        mutate(proposal.read_text(encoding="utf-8")),
                        encoding="utf-8",
                    )

                    try:
                        issues = validate_precommit(
                            repo_root,
                            repo_root / PLAN_RELATIVE,
                        )
                    except PrecommitRuntimeError as error:
                        self.fail(
                            "deterministic proposal defect must be an issue, "
                            f"not runtime: {error}"
                        )

                self.assertTrue(
                    any(
                        issue.code == "EVIDENCE_INCOMPLETE"
                        and proposal.relative_to(repo_root).as_posix()
                        == issue.path.as_posix()
                        for issue in issues
                    )
                )

    def test_precommit_requires_proposal_linked_to_selected_plan_task(self) -> None:
        # Break caught: task-linked approval is omitted from evidence/scope/message.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            current = write_proposal(
                repo_root,
                proposal_id="CP-02",
                task_id="M01-T01",
            )

            issues = validate_precommit(repo_root, repo_root / PLAN_RELATIVE)

        current_path = current.relative_to(repo_root).as_posix()
        self.assertTrue(
            any(
                issue.code == "EVIDENCE_INCOMPLETE"
                and "approved proposals" in issue.message
                for issue in issues
            )
        )
        self.assertTrue(
            any(
                issue.code == "STAGED_SCOPE_INVALID"
                and current_path in issue.message
                for issue in issues
            )
        )
        self.assertTrue(
            any(
                issue.code == "COMMIT_MESSAGE_INVALID"
                and "Change-Proposals" in issue.message
                for issue in issues
            )
        )

    def test_repository_validation_still_reports_pending_historical_proposal(
        self,
    ) -> None:
        # Break caught: milestone filtering suppresses repository workflow issues.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            write_proposal(
                repo_root,
                proposal_id="CP-02",
                task_id="M00-T01",
                status="Pending",
                gate="Pending",
            )

            issues = validate_repository(repo_root)

        self.assertTrue(
            any(issue.code == "CHANGE_PROPOSAL_PENDING" for issue in issues)
        )

    def test_custom_proposal_template_requires_current_task_id_everywhere(
        self,
    ) -> None:
        # Break caught: custom filenames evade authoritative proposal ID checks.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(
                temp_dir,
                custom_proposal_template=True,
            )
            current = write_proposal(
                repo_root,
                proposal_id="CP-02",
                task_id="M01-T01",
                filename="sample-change-02-additional.md",
            )

            issues = validate_precommit(repo_root, repo_root / PLAN_RELATIVE)

        current_path = current.relative_to(repo_root).as_posix()
        self.assertTrue(
            any(
                issue.code == "EVIDENCE_INCOMPLETE"
                and "approved proposals" in issue.message
                for issue in issues
            )
        )
        self.assertTrue(
            any(
                issue.code == "STAGED_SCOPE_INVALID"
                and current_path in issue.message
                for issue in issues
            )
        )
        self.assertTrue(
            any(
                issue.code == "COMMIT_MESSAGE_INVALID"
                and "CP-02" in issue.message
                for issue in issues
            )
        )

    def test_custom_proposal_template_exact_current_ids_pass(self) -> None:
        # Break caught: configured proposal IDs still use the legacy -cpNN- shape.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(
                temp_dir,
                custom_proposal_template=True,
            )
            current = write_proposal(
                repo_root,
                proposal_id="CP-02",
                task_id="M01-T01",
                filename="sample-change-02-additional.md",
            )
            write_proposal(
                repo_root,
                proposal_id="CP-03",
                task_id="M00-T01",
                filename="sample-change-03-historical.md",
            )
            plan_path = repo_root / PLAN_RELATIVE
            content = (
                plan_path.read_text(encoding="utf-8")
                .replace(
                    "- Approved proposals: CP-01",
                    "- Approved proposals: CP-01, CP-02",
                )
                .replace(
                    f"| `{CUSTOM_CP01.as_posix()}` | Approved proposal |",
                    f"| `{CUSTOM_CP01.as_posix()}` | Approved proposal |\n"
                    f"| `{current.relative_to(repo_root).as_posix()}` | "
                    "Current approved proposal |",
                )
                .replace(
                    "Change-Proposals: CP-01",
                    "Change-Proposals: CP-01, CP-02",
                )
            )
            plan_path.write_text(content, encoding="utf-8")
            require_git(
                repo_root,
                "add",
                "--",
                PLAN_RELATIVE.as_posix(),
                current.relative_to(repo_root).as_posix(),
            )
            before = git_snapshot(repo_root)

            issues = validate_precommit(repo_root, plan_path)

            after = git_snapshot(repo_root)

        self.assertEqual([], issues)
        self.assertEqual(before, after)

    def test_duplicate_current_proposal_id_is_deterministic_evidence_issue(
        self,
    ) -> None:
        # Break caught: duplicate CP IDs become a duplicated trailer requirement.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            first = write_proposal(
                repo_root,
                proposal_id="CP-02",
                task_id="M01-T01",
                filename="sample-cp02-first.md",
            )
            second = write_proposal(
                repo_root,
                proposal_id="CP-02",
                task_id="M01-T02",
                filename="sample-cp02-second.md",
            )
            plan_path = repo_root / PLAN_RELATIVE
            content = (
                plan_path.read_text(encoding="utf-8")
                .replace(
                    "- Approved proposals: CP-01",
                    "- Approved proposals: CP-01, CP-02",
                )
                .replace(
                    "| `docs/changes/sample-cp01-traceability.md` | "
                    "Approved proposal |",
                    "| `docs/changes/sample-cp01-traceability.md` | "
                    "Approved proposal |\n"
                    f"| `{first.relative_to(repo_root).as_posix()}` | "
                    "First current proposal |\n"
                    f"| `{second.relative_to(repo_root).as_posix()}` | "
                    "Second current proposal |",
                )
                .replace(
                    "Change-Proposals: CP-01",
                    "Change-Proposals: CP-01, CP-02",
                )
            )
            plan_path.write_text(content, encoding="utf-8")
            require_git(
                repo_root,
                "add",
                "--",
                PLAN_RELATIVE.as_posix(),
                first.relative_to(repo_root).as_posix(),
                second.relative_to(repo_root).as_posix(),
            )

            issues = validate_precommit(repo_root, plan_path)

        duplicate_issues = [
            issue
            for issue in issues
            if issue.code == "EVIDENCE_INCOMPLETE"
            and "duplicate approved proposal ID: CP-02" in issue.message
        ]
        self.assertEqual(1, len(duplicate_issues))
        self.assertFalse(
            any(
                issue.code == "COMMIT_MESSAGE_INVALID"
                and "CP-02, CP-02" in issue.message
                for issue in issues
            )
        )

    def test_current_and_historical_duplicate_proposal_id_is_ambiguous(
        self,
    ) -> None:
        # Break caught: duplicate IDs are checked only after milestone filtering.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(
                temp_dir,
                custom_proposal_template=True,
            )
            current = write_proposal(
                repo_root,
                proposal_id="CP-02",
                task_id="M01-T01",
                filename="sample-change-02-current.md",
            )
            historical = write_proposal(
                repo_root,
                proposal_id="CP-02",
                task_id="M00-T01",
                filename="sample-change-02-historical.md",
            )
            plan_path = repo_root / PLAN_RELATIVE
            content = (
                plan_path.read_text(encoding="utf-8")
                .replace(
                    "- Approved proposals: CP-01",
                    "- Approved proposals: CP-01, CP-02",
                )
                .replace(
                    f"| `{CUSTOM_CP01.as_posix()}` | Approved proposal |",
                    f"| `{CUSTOM_CP01.as_posix()}` | Approved proposal |\n"
                    f"| `{current.relative_to(repo_root).as_posix()}` | "
                    "Current approved proposal |",
                )
                .replace(
                    "Change-Proposals: CP-01",
                    "Change-Proposals: CP-01, CP-02",
                )
            )
            plan_path.write_text(content, encoding="utf-8")
            require_git(
                repo_root,
                "add",
                "--",
                PLAN_RELATIVE.as_posix(),
                current.relative_to(repo_root).as_posix(),
            )

            issues = validate_precommit(repo_root, plan_path)

        duplicates = [
            issue
            for issue in issues
            if issue.code == "EVIDENCE_INCOMPLETE"
            and "duplicate approved proposal ID: CP-02" in issue.message
        ]
        self.assertEqual(1, len(duplicates))
        self.assertFalse(
            any(
                issue.code == "STAGED_SCOPE_INVALID"
                and historical.relative_to(repo_root).as_posix()
                in issue.message
                for issue in issues
            )
        )
        self.assertFalse(
            any(
                issue.code == "COMMIT_MESSAGE_INVALID"
                and "CP-02, CP-02" in issue.message
                for issue in issues
            )
        )

    def test_precommit_is_read_only_and_preserves_unrelated_unstaged_file(
        self,
    ) -> None:
        # Break caught: validation mutates the worktree, index, HEAD, or remotes.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            require_git(
                repo_root,
                "remote",
                "add",
                "origin",
                "https://example.invalid/repo.git",
            )
            before = git_snapshot(repo_root)
            notes_before = (repo_root / "user-notes.txt").read_bytes()

            issues = validate_precommit(repo_root, repo_root / PLAN_RELATIVE)

            after = git_snapshot(repo_root)
            notes_after = (repo_root / "user-notes.txt").read_bytes()

        self.assertEqual([], issues)
        self.assertEqual(before, after)
        self.assertEqual(notes_before, notes_after)

    def test_precommit_issues_have_stable_path_line_code_order(self) -> None:
        # Break caught: composition order leaks into the public diagnostic order.
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = prepare_repository(temp_dir)
            plan_path = repo_root / PLAN_RELATIVE
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8")
                .replace(
                    "- Baseline dirty paths: None",
                    "- Baseline dirty paths: src/app.py",
                )
                .replace(
                    "feat(evidence): validate milestone delivery",
                    "invalid subject",
                ),
                encoding="utf-8",
            )
            require_git(repo_root, "add", "--", "user-notes.txt")

            issues = validate_precommit(repo_root, plan_path)

        keys = [
            (issue.path.as_posix().casefold(), issue.line, issue.code)
            for issue in issues
        ]
        self.assertGreaterEqual(len(keys), 3)
        self.assertEqual(sorted(keys), keys)


if __name__ == "__main__":
    unittest.main()
