from __future__ import annotations

import unittest
from io import StringIO
from pathlib import Path
import re
import tempfile
from unittest import mock

from tools import verify_npx_install


REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
LICENSE = REPO_ROOT / "LICENSE"
GIT_ATTRIBUTES = REPO_ROOT / ".gitattributes"
INTERACTIVE_COMMAND = (
    "npx skills@latest add WeirdFishBK201/tracing-spec-to-code"
)
NON_INTERACTIVE_COMMAND = (
    "npx skills@latest add WeirdFishBK201/tracing-spec-to-code "
    "--skill tracing-spec-to-code --agent codex --global --copy --yes"
)


class ReadmeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.readme = README.read_text(encoding="utf-8")

    def _quick_start_install_commands(self) -> list[str]:
        quick_start = self.readme.split("## Quick Start\n", 1)[1].split(
            "\n## ", 1
        )[0]
        commands: list[str] = []
        in_code_block = False
        for line in quick_start.splitlines():
            if line.startswith("```"):
                in_code_block = not in_code_block
            elif in_code_block and line.startswith("npx "):
                commands.append(line)
        return commands

    def test_documents_interactive_github_installation(self) -> None:
        self.assertEqual(
            INTERACTIVE_COMMAND,
            self._quick_start_install_commands()[0],
        )

    def test_documents_non_interactive_codex_global_installation(self) -> None:
        self.assertEqual(
            NON_INTERACTIVE_COMMAND,
            self._quick_start_install_commands()[1],
        )

    def test_user_facing_install_commands_are_exact_and_latest_only(self) -> None:
        self.assertEqual(
            [INTERACTIVE_COMMAND, NON_INTERACTIVE_COMMAND],
            self._quick_start_install_commands(),
        )
        for command in self._quick_start_install_commands():
            self.assertIn("skills@latest", command)
            self.assertIsNone(re.search(r"skills@\d", command))

    def test_documents_verified_requirements_and_source(self) -> None:
        self.assertIn("skills@1.5.21", self.readme)
        self.assertIn("Node.js 22.20.0 or newer", self.readme)
        self.assertIn("WeirdFishBK201/tracing-spec-to-code", self.readme)

    def test_documents_offline_python_installer(self) -> None:
        self.assertIn("Offline installation from a local clone", self.readme)
        self.assertIn("python tools/install.py --client codex", self.readme)

    def test_no_longer_defers_github_or_npx_installation(self) -> None:
        self.assertNotIn("intentionally deferred", self.readme)
        self.assertNotIn("post-M05 long-term goal", self.readme)

    def test_license_has_mit_copyright_metadata(self) -> None:
        self.assertTrue(LICENSE.exists())
        license_text = LICENSE.read_text(encoding="utf-8")
        self.assertIn("MIT License", license_text)
        self.assertIn("Copyright (c) 2026 WeirdFishBK201", license_text)


class NpxAcceptanceToolTests(unittest.TestCase):
    def test_canonical_skill_tree_uses_lf_checkout_bytes(self) -> None:
        self.assertTrue(GIT_ATTRIBUTES.exists())
        self.assertIn(
            "skills/tracing-spec-to-code/** text eol=lf",
            GIT_ATTRIBUTES.read_text(encoding="utf-8").splitlines(),
        )

    def test_build_command_uses_pinned_non_interactive_copy_install(self) -> None:
        command = verify_npx_install.build_command(
            "candidate-source", "project", "C:/tools/npx.cmd"
        )

        self.assertEqual(
            (
                "C:/tools/npx.cmd",
                "--yes",
                "skills@1.5.21",
                "add",
                "candidate-source",
                "--skill",
                "tracing-spec-to-code",
                "--agent",
                "codex",
                "--copy",
                "--yes",
            ),
            command,
        )

    def test_build_command_adds_global_only_for_global_scope(self) -> None:
        command = verify_npx_install.build_command("source", "global", "npx")

        self.assertEqual(
            (
                "npx", "--yes", "skills@1.5.21", "add", "source",
                "--skill", "tracing-spec-to-code", "--agent", "codex",
                "--global", "--copy", "--yes",
            ),
            command,
        )

    def test_build_isolated_environment_uses_only_isolated_user_roots(self) -> None:
        base = Path("C:/acceptance")
        user_root = base / "user"

        environment = verify_npx_install.build_isolated_environment(
            base, user_root
        )

        self.assertEqual(str(user_root), environment["HOME"])
        self.assertEqual(str(user_root), environment["USERPROFILE"])
        self.assertEqual(str(user_root / ".config"), environment["XDG_CONFIG_HOME"])
        self.assertEqual(str(user_root / ".cache"), environment["XDG_CACHE_HOME"])
        self.assertEqual(str(user_root / "AppData" / "Roaming"), environment["APPDATA"])
        self.assertEqual("1", environment["GIT_CONFIG_COUNT"])
        self.assertEqual("core.autocrlf", environment["GIT_CONFIG_KEY_0"])
        self.assertEqual("false", environment["GIT_CONFIG_VALUE_0"])

    def test_expected_target_matches_external_client_scope_layout(self) -> None:
        project_root = Path("C:/acceptance/project")
        user_root = Path("C:/acceptance/user")

        self.assertEqual(
            project_root / ".agents" / "skills" / "tracing-spec-to-code",
            verify_npx_install.expected_target(project_root, user_root, "project"),
        )
        self.assertEqual(
            user_root / ".agents" / "skills" / "tracing-spec-to-code",
            verify_npx_install.expected_target(project_root, user_root, "global"),
        )

    def test_compare_manifests_ignores_runtime_cache_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            target = Path(temporary) / "target"
            source.mkdir()
            target.mkdir()
            (source / "SKILL.md").write_text("canonical", encoding="utf-8")
            (target / "SKILL.md").write_text("canonical", encoding="utf-8")
            cache = target / "__pycache__"
            cache.mkdir()
            (cache / "generated.pyc").write_bytes(b"runtime-only")

            self.assertIsNone(verify_npx_install.compare_manifests(source, target))

    def test_compare_manifests_reports_deterministic_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            target = Path(temporary) / "target"
            source.mkdir()
            target.mkdir()
            (source / "SKILL.md").write_text("canonical", encoding="utf-8")
            (target / "SKILL.md").write_text("different", encoding="utf-8")

            self.assertEqual(
                "manifest mismatch: SKILL.md differs",
                verify_npx_install.compare_manifests(source, target),
            )

    def test_run_scope_reports_subprocess_failure_without_using_real_npx(self) -> None:
        completed = mock.Mock(returncode=9)
        with mock.patch.object(verify_npx_install.shutil, "which", return_value="npx"), mock.patch.object(
            verify_npx_install.subprocess, "run", return_value=completed
        ) as run:
            result = verify_npx_install.run_scope("source", "project")

        self.assertEqual("project: npx exited with status 9", result)
        command = run.call_args.args[0]
        self.assertEqual("npx", command[0])
        self.assertFalse(run.call_args.kwargs["shell"])
        self.assertIs(verify_npx_install.subprocess.PIPE, run.call_args.kwargs["stdout"])
        self.assertIs(verify_npx_install.subprocess.PIPE, run.call_args.kwargs["stderr"])
        self.assertFalse(run.call_args.kwargs["check"])

    def test_main_maps_acceptance_and_runtime_failures_to_expected_exits(self) -> None:
        with mock.patch.object(
            verify_npx_install, "run_scope", return_value="project: missing target"
        ), mock.patch("sys.stderr"):
            self.assertEqual(1, verify_npx_install.main(["--source", "source"]))
        with mock.patch.object(
            verify_npx_install, "run_scope", side_effect=RuntimeError("boom")
        ), mock.patch("sys.stderr"):
            self.assertEqual(2, verify_npx_install.main(["--source", "source"]))

    def test_main_reports_success_for_all_project_and_global_scopes(self) -> None:
        cases = (
            ([], ("project", "global"), "VERIFIED project\nVERIFIED global\n"),
            (["--scope", "project"], ("project",), "VERIFIED project\n"),
            (["--scope", "global"], ("global",), "VERIFIED global\n"),
        )
        for arguments, expected_scopes, expected_output in cases:
            with self.subTest(arguments=arguments), mock.patch.object(
                verify_npx_install, "run_scope", return_value=None
            ) as run_scope, mock.patch("sys.stdout", new_callable=StringIO) as stdout:
                self.assertEqual(
                    0,
                    verify_npx_install.main(["--source", "source", *arguments]),
                )
                self.assertEqual(expected_output, stdout.getvalue())
                self.assertEqual(
                    [mock.call("source", scope) for scope in expected_scopes],
                    run_scope.call_args_list,
                )

    def test_main_invalid_scope_exits_two_before_running_acceptance(self) -> None:
        with mock.patch.object(verify_npx_install, "run_scope") as run_scope, mock.patch(
            "sys.stderr", new_callable=StringIO
        ) as stderr:
            with self.assertRaises(SystemExit) as raised:
                verify_npx_install.main(["--source", "source", "--scope", "invalid"])

        self.assertEqual(2, raised.exception.code)
        self.assertIn("invalid choice", stderr.getvalue())
        run_scope.assert_not_called()


if __name__ == "__main__":
    unittest.main()
