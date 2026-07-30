from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import install
from tools.distribution import build_manifest


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SCRIPT = REPO_ROOT / "tools" / "install.py"
CANONICAL_SOURCE = REPO_ROOT / "skills" / "tracing-spec-to-code"


def distributable_manifest(source: Path) -> tuple[object, ...]:
    return tuple(
        entry
        for entry in build_manifest(source)
        if "__pycache__" not in Path(entry.relative_path).parts
        and Path(entry.relative_path).suffix not in {".pyc", ".pyo"}
    )


class InstallCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.base = Path(self.temp_dir.name)
        self.explicit_root = self.base / "explicit-root"
        self.explicit_root.mkdir()
        self.fake_home = self.base / "forbidden-home"
        self.fake_home.mkdir()
        self.home_sentinel = self.fake_home / "sentinel.txt"
        self.home_sentinel.write_text("untouched", encoding="utf-8")

    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update(
            {
                "HOME": str(self.fake_home),
                "USERPROFILE": str(self.fake_home),
                "XDG_CONFIG_HOME": str(self.fake_home / "xdg"),
                "APPDATA": str(self.fake_home / "appdata"),
                "LOCALAPPDATA": str(self.fake_home / "localappdata"),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )
        return subprocess.run(
            [sys.executable, str(INSTALL_SCRIPT), *arguments],
            cwd=REPO_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def assert_fake_home_untouched(self) -> None:
        self.assertEqual(
            ("sentinel.txt",),
            tuple(path.name for path in self.fake_home.iterdir()),
        )
        self.assertEqual(
            "untouched",
            self.home_sentinel.read_text(encoding="utf-8"),
        )

    def test_project_install_reports_verified_result_and_uses_explicit_root(
        self,
    ) -> None:
        result = self.run_cli(
            "--client",
            "codex",
            "--scope",
            "project",
            "--project-root",
            str(self.explicit_root),
        )
        target = (
            self.explicit_root.resolve()
            / ".agents"
            / "skills"
            / "tracing-spec-to-code"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            (
                f"installed client=codex scope=project target={target} "
                f"files={len(distributable_manifest(CANONICAL_SOURCE))}\n"
            ),
            result.stdout,
        )
        self.assertEqual("", result.stderr)
        self.assertEqual(
            distributable_manifest(CANONICAL_SOURCE),
            build_manifest(target),
        )
        self.assert_fake_home_untouched()

    def test_user_install_uses_only_explicit_home_root(self) -> None:
        result = self.run_cli(
            "--client",
            "cline",
            "--scope",
            "user",
            "--home-root",
            str(self.explicit_root),
        )
        target = (
            self.explicit_root.resolve()
            / ".cline"
            / "skills"
            / "tracing-spec-to-code"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(
            f"client=cline scope=user target={target}",
            result.stdout,
        )
        self.assertEqual(
            distributable_manifest(CANONICAL_SOURCE),
            build_manifest(target),
        )
        self.assert_fake_home_untouched()

    def test_unknown_client_is_policy_exit_one(self) -> None:
        result = self.run_cli(
            "--client",
            "unknown-client",
            "--scope",
            "project",
            "--project-root",
            str(self.explicit_root),
        )

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertEqual(
            "ERROR TARGET_INVALID: unknown client: unknown-client\n",
            result.stderr,
        )
        self.assert_fake_home_untouched()

    def test_existing_target_is_policy_exit_one_and_preserves_sentinel(
        self,
    ) -> None:
        target = (
            self.explicit_root
            / ".agents"
            / "skills"
            / "tracing-spec-to-code"
        )
        target.mkdir(parents=True)
        sentinel = target / "sentinel.txt"
        sentinel.write_text("keep me", encoding="utf-8")

        result = self.run_cli(
            "--client",
            "codex",
            "--scope",
            "project",
            "--project-root",
            str(self.explicit_root),
        )

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertEqual(
            f"ERROR TARGET_EXISTS: install target already exists [{target.resolve()}]\n",
            result.stderr,
        )
        self.assertEqual("keep me", sentinel.read_text(encoding="utf-8"))
        self.assert_fake_home_untouched()

    def test_only_scope_matching_explicit_root_form_is_accepted(self) -> None:
        invalid_arguments = (
            (
                "--client",
                "codex",
                "--scope",
                "project",
            ),
            (
                "--client",
                "codex",
                "--scope",
                "user",
            ),
            (
                "--client",
                "codex",
                "--scope",
                "project",
                "--home-root",
                str(self.explicit_root),
            ),
            (
                "--client",
                "codex",
                "--scope",
                "user",
                "--project-root",
                str(self.explicit_root),
            ),
            (
                "--client",
                "codex",
                "--scope",
                "project",
                "--project-root",
                str(self.explicit_root),
                "--home-root",
                str(self.explicit_root),
            ),
        )

        for arguments in invalid_arguments:
            with self.subTest(arguments=arguments):
                result = self.run_cli(*arguments)

                self.assertEqual(2, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertIn("error:", result.stderr)
                self.assert_fake_home_untouched()

    def test_unexpected_runtime_error_is_exit_two(self) -> None:
        stderr = io.StringIO()
        with (
            mock.patch(
                "tools.install.install_skill",
                side_effect=RuntimeError("unexpected failure"),
            ),
            contextlib.redirect_stderr(stderr),
        ):
            exit_code = install.main(
                [
                    "--client",
                    "codex",
                    "--scope",
                    "project",
                    "--project-root",
                    str(self.explicit_root),
                ]
            )

        self.assertEqual(2, exit_code)
        self.assertEqual(
            "ERROR RUNTIME: unexpected failure\n",
            stderr.getvalue(),
        )
        self.assert_fake_home_untouched()

    @unittest.skipUnless(
        hasattr(BaseException, "add_note"),
        "BaseException.add_note requires Python 3.11+",
    )
    def test_runtime_error_includes_python_cleanup_notes(self) -> None:
        runtime_error = RuntimeError("unexpected failure")
        runtime_error.add_note(
            "cleanup failed: cannot remove workspace [C:/safe/workspace]"
        )
        stderr = io.StringIO()
        with (
            mock.patch(
                "tools.install.install_skill",
                side_effect=runtime_error,
            ),
            contextlib.redirect_stderr(stderr),
        ):
            exit_code = install.main(
                [
                    "--client",
                    "codex",
                    "--scope",
                    "project",
                    "--project-root",
                    str(self.explicit_root),
                ]
            )

        self.assertEqual(2, exit_code)
        self.assertEqual(
            (
                "ERROR RUNTIME: unexpected failure; "
                "cleanup failed: cannot remove workspace "
                "[C:/safe/workspace]\n"
            ),
            stderr.getvalue(),
        )

    def test_runtime_error_includes_python310_cleanup_fallback(self) -> None:
        runtime_error = RuntimeError("unexpected failure")
        runtime_error.cleanup_failure = (  # type: ignore[attr-defined]
            "cleanup failed: cannot remove target [C:/safe/target]"
        )
        stderr = io.StringIO()
        with (
            mock.patch(
                "tools.install.install_skill",
                side_effect=runtime_error,
            ),
            contextlib.redirect_stderr(stderr),
        ):
            exit_code = install.main(
                [
                    "--client",
                    "codex",
                    "--scope",
                    "project",
                    "--project-root",
                    str(self.explicit_root),
                ]
            )

        self.assertEqual(2, exit_code)
        self.assertEqual(
            (
                "ERROR RUNTIME: unexpected failure; "
                "cleanup failed: cannot remove target [C:/safe/target]\n"
            ),
            stderr.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
