from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "tracing-spec-to-code"
    / "scripts"
)
sys.path.insert(0, str(SCRIPTS_DIR))

from tstc.config import ConfigError, load_config


class LoadConfigTests(unittest.TestCase):
    def test_defaults_resolve_from_repository_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()

            config = load_config(repo_root)

            self.assertIsNotNone(config, "load_config must return resolved defaults")
            self.assertEqual(repo_root, config.repo_root)
            self.assertEqual(repo_root / "docs" / "specs", config.spec_dir)
            self.assertEqual(repo_root / "docs" / "plans", config.plan_dir)
            self.assertEqual(repo_root / "docs" / "changes", config.change_dir)
            self.assertEqual(repo_root.name, config.feature_slug)
            self.assertEqual("{feature}-spec.md", config.spec_filename_template)
            self.assertEqual("{feature}-roadmap.md", config.roadmap_filename_template)
            self.assertEqual(
                "{feature}-m{milestone}-{milestone_slug}.md",
                config.milestone_plan_filename_template,
            )
            self.assertEqual(
                "{feature}-cr{change_request}-{change_request_slug}.md",
                config.change_request_filename_template,
            )

    def test_valid_config_overrides_directories_slug_and_templates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            config_data = {
                "spec_dir": "requirements",
                "plan_dir": "delivery/plans",
                "change_dir": "delivery/changes",
                "feature_slug": "checkout",
                "spec_filename_template": "spec-{feature}.md",
                "roadmap_filename_template": "roadmap-{feature}.md",
                "milestone_plan_filename_template": (
                    "m{milestone}-{feature}-{milestone_slug}.md"
                ),
                "change_request_filename_template": (
                    "cr{change_request}-{feature}-{change_request_slug}.md"
                ),
            }
            (repo_root / ".tracing-spec-to-code.json").write_text(
                json.dumps(config_data),
                encoding="utf-8",
            )

            config = load_config(repo_root)

            self.assertEqual(repo_root / "requirements", config.spec_dir)
            self.assertEqual(repo_root / "delivery" / "plans", config.plan_dir)
            self.assertEqual(repo_root / "delivery" / "changes", config.change_dir)
            self.assertEqual("checkout", config.feature_slug)
            self.assertEqual("spec-{feature}.md", config.spec_filename_template)
            self.assertEqual(
                "roadmap-{feature}.md",
                config.roadmap_filename_template,
            )
            self.assertEqual(
                "m{milestone}-{feature}-{milestone_slug}.md",
                config.milestone_plan_filename_template,
            )
            self.assertEqual(
                "cr{change_request}-{feature}-{change_request_slug}.md",
                config.change_request_filename_template,
            )

    def test_invalid_json_reports_stable_config_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            config_path = repo_root / ".tracing-spec-to-code.json"
            config_path.write_text("{", encoding="utf-8")

            try:
                load_config(repo_root)
            except Exception as error:
                raised = error
            else:
                self.fail("invalid JSON must raise ConfigError")

            self.assertIsInstance(raised, ConfigError)
            self.assertEqual("CFG_INVALID_JSON", raised.code)
            self.assertEqual(config_path, raised.path)

    def test_non_utf8_config_reports_stable_config_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            config_path = repo_root / ".tracing-spec-to-code.json"
            config_path.write_bytes(b"\xff")

            with self.assertRaises(ConfigError) as raised:
                load_config(repo_root)

            self.assertEqual("CFG_INVALID_JSON", raised.exception.code)
            self.assertEqual(config_path, raised.exception.path)

    def test_unknown_key_is_rejected_instead_of_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            config_path = repo_root / ".tracing-spec-to-code.json"
            config_path.write_text(
                json.dumps({"unexpected": True}),
                encoding="utf-8",
            )

            with self.assertRaises(ConfigError) as raised:
                load_config(repo_root)

            self.assertEqual("CFG_UNKNOWN_KEY", raised.exception.code)
            self.assertEqual(config_path, raised.exception.path)
            self.assertIn("unexpected", raised.exception.message)

    def test_change_request_config_key_is_not_a_compatibility_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            config_path = repo_root / ".tracing-spec-to-code.json"
            old_key = "change_" + "proposal_filename_template"
            config_path.write_text(
                json.dumps(
                    {
                        old_key: (
                            "{feature}-cp{request}-{request_slug}.md"
                        )
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ConfigError) as raised:
                load_config(repo_root)

            self.assertEqual("CFG_UNKNOWN_KEY", raised.exception.code)
            self.assertIn(
                old_key,
                raised.exception.message,
            )

    def test_directory_override_must_stay_inside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            cases = {
                "absolute": str(repo_root.parent / "absolute-outside"),
                "parent traversal": "../outside",
            }

            for label, configured_path in cases.items():
                with self.subTest(label=label):
                    config_path = repo_root / ".tracing-spec-to-code.json"
                    config_path.write_text(
                        json.dumps({"spec_dir": configured_path}),
                        encoding="utf-8",
                    )

                    with self.assertRaises(ConfigError) as raised:
                        load_config(repo_root)

                    self.assertEqual(
                        "CFG_PATH_OUTSIDE_REPO",
                        raised.exception.code,
                    )
                    self.assertEqual(config_path, raised.exception.path)

    def test_invalid_filename_template_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            cases = {
                "unknown placeholder": {
                    "spec_filename_template": "{feature}-{unknown}.md",
                },
                "missing placeholder": {
                    "roadmap_filename_template": "roadmap.md",
                },
                "path injection": {
                    "spec_filename_template": "../{feature}-spec.md",
                },
                "windows path injection": {
                    "spec_filename_template": "nested\\{feature}-spec.md",
                },
                "non-markdown suffix": {
                    "spec_filename_template": "{feature}-spec.txt",
                },
                "incomplete milestone template": {
                    "milestone_plan_filename_template": (
                        "{feature}-m{milestone}.md"
                    ),
                },
                "incomplete change request template": {
                    "change_request_filename_template": (
                        "{feature}-cr{change_request}.md"
                    ),
                },
            }

            for label, config_data in cases.items():
                with self.subTest(label=label):
                    config_path = repo_root / ".tracing-spec-to-code.json"
                    config_path.write_text(
                        json.dumps(config_data),
                        encoding="utf-8",
                    )

                    with self.assertRaises(ConfigError) as raised:
                        load_config(repo_root)

                    self.assertEqual(
                        "CFG_TEMPLATE_INVALID",
                        raised.exception.code,
                    )
                    self.assertEqual(config_path, raised.exception.path)

    def test_custom_config_path_is_relative_to_repository_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            config_path = repo_root / "config" / "artifact-contracts.json"
            config_path.parent.mkdir()
            config_path.write_text(
                json.dumps({"feature_slug": "custom-feature"}),
                encoding="utf-8",
            )

            config = load_config(
                repo_root,
                Path("config/artifact-contracts.json"),
            )

            self.assertEqual("custom-feature", config.feature_slug)

    def test_config_path_must_stay_inside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir).resolve()
            repo_root = base / "repo"
            repo_root.mkdir()
            outside_path = base / "outside.json"
            outside_path.write_text("{}", encoding="utf-8")

            for candidate in (Path("../outside.json"), outside_path):
                with self.subTest(candidate=candidate):
                    with self.assertRaises(ConfigError) as raised:
                        load_config(repo_root, candidate)

                    self.assertEqual(
                        "CFG_PATH_OUTSIDE_REPO",
                        raised.exception.code,
                    )
                    self.assertEqual(outside_path, raised.exception.path)

    def test_feature_slug_cannot_inject_a_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            config_path = repo_root / ".tracing-spec-to-code.json"
            config_path.write_text(
                json.dumps({"feature_slug": "../outside"}),
                encoding="utf-8",
            )

            with self.assertRaises(ConfigError) as raised:
                load_config(repo_root)

            self.assertEqual(
                "CFG_PATH_OUTSIDE_REPO",
                raised.exception.code,
            )
            self.assertEqual(config_path, raised.exception.path)

    def test_explicit_missing_config_does_not_fall_back_to_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            config_path = Path("config/missing.json")

            with self.assertRaises(ConfigError) as raised:
                load_config(repo_root, config_path)

            self.assertEqual("CFG_INVALID_JSON", raised.exception.code)
            self.assertEqual(
                repo_root / config_path,
                raised.exception.path,
            )
            self.assertIn("does not exist", raised.exception.message)

    def test_config_root_must_be_a_json_object(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            config_path = repo_root / ".tracing-spec-to-code.json"
            config_path.write_text("[]", encoding="utf-8")

            try:
                load_config(repo_root)
            except Exception as error:
                raised = error
            else:
                self.fail("a JSON array must not be accepted as config")

            self.assertIsInstance(raised, ConfigError)
            self.assertEqual("CFG_INVALID_JSON", raised.code)
            self.assertEqual(config_path, raised.path)

    def test_directory_values_must_be_strings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            config_path = repo_root / ".tracing-spec-to-code.json"

            for value in (None, 42, []):
                with self.subTest(value=value):
                    config_path.write_text(
                        json.dumps({"spec_dir": value}),
                        encoding="utf-8",
                    )
                    try:
                        load_config(repo_root)
                    except Exception as error:
                        raised = error
                    else:
                        self.fail("non-string directory must be rejected")

                    self.assertIsInstance(raised, ConfigError)
                    self.assertEqual("CFG_INVALID_JSON", raised.code)
                    self.assertEqual(config_path, raised.path)


if __name__ == "__main__":
    unittest.main()
