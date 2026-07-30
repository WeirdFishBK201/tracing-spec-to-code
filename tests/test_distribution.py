from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import tools.distribution as distribution_module
from tools.distribution import (
    ClientSpec,
    DistributionError,
    InstallResult,
    ManifestEntry,
    build_manifest,
    install_skill,
    load_registry,
    resolve_install_target,
)


APPROVED_CLIENTS = (
    ClientSpec(
        id="codex",
        display_name="Codex",
        level=1,
        project_path=".agents/skills",
        user_path=".agents/skills",
        verification="install-discovery",
    ),
    ClientSpec(
        id="claude-code",
        display_name="Claude Code",
        level=1,
        project_path=".claude/skills",
        user_path=".claude/skills",
        verification="install-discovery",
    ),
    ClientSpec(
        id="github-copilot",
        display_name="GitHub Copilot CLI",
        level=1,
        project_path=".github/skills",
        user_path=".copilot/skills",
        verification="install-discovery",
    ),
    ClientSpec(
        id="antigravity",
        display_name="Antigravity",
        level=1,
        project_path=".agent/skills",
        user_path=".gemini/antigravity/skills",
        verification="install-discovery",
    ),
    ClientSpec(
        id="gemini-cli",
        display_name="Gemini CLI",
        level=1,
        project_path=".gemini/skills",
        user_path=".gemini/skills",
        verification="install-discovery",
    ),
    ClientSpec(
        id="cursor",
        display_name="Cursor",
        level=2,
        project_path=".cursor/skills",
        user_path=".cursor/skills",
        verification="structure-smoke",
    ),
    ClientSpec(
        id="windsurf",
        display_name="Windsurf/Cascade",
        level=2,
        project_path=".windsurf/skills",
        user_path=".codeium/windsurf/skills",
        verification="structure-smoke",
    ),
    ClientSpec(
        id="cline",
        display_name="Cline",
        level=2,
        project_path=".cline/skills",
        user_path=".cline/skills",
        verification="structure-smoke",
    ),
)


def remove_windows_junction(junction: Path) -> None:
    try:
        os.rmdir(junction)
    except FileNotFoundError:
        pass


def create_windows_junction(
    test_case: unittest.TestCase,
    junction: Path,
    target: Path,
) -> None:
    result = subprocess.run(
        [
            "cmd.exe",
            "/d",
            "/c",
            "mklink",
            "/J",
            str(junction),
            str(target),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        test_case.skipTest(
            "cannot create Windows junction: "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    test_case.addCleanup(remove_windows_junction, junction)


class RegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.registry_path = Path(self.temp_dir.name) / "clients.json"

    def write_registry(self, data: object) -> None:
        self.registry_path.write_text(json.dumps(data), encoding="utf-8")

    def valid_registry(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "clients": [
                {
                    "id": "sample-client",
                    "display_name": "Sample Client",
                    "level": 1,
                    "project_path": ".sample/skills",
                    "user_path": ".sample/skills",
                    "verification": "install-discovery",
                }
            ],
        }

    def assert_registry_invalid(self) -> DistributionError:
        with self.assertRaises(DistributionError) as raised:
            load_registry(self.registry_path)
        self.assertEqual("REGISTRY_INVALID", raised.exception.code)
        self.assertEqual(self.registry_path, raised.exception.path)
        return raised.exception

    def test_repository_registry_matches_the_approved_client_matrix(self) -> None:
        repository_registry = (
            Path(__file__).resolve().parents[1] / "tools" / "clients.json"
        )

        clients = load_registry(repository_registry)

        self.assertEqual(APPROVED_CLIENTS, clients)

    def test_registry_rejects_unknown_and_missing_keys(self) -> None:
        cases: dict[str, dict[str, object]] = {}

        unknown_top_level = self.valid_registry()
        unknown_top_level["unexpected"] = True
        cases["unknown top-level key"] = unknown_top_level

        missing_top_level = self.valid_registry()
        del missing_top_level["schema_version"]
        cases["missing top-level key"] = missing_top_level

        unknown_client = self.valid_registry()
        unknown_client["clients"][0]["unexpected"] = True  # type: ignore[index]
        cases["unknown client key"] = unknown_client

        missing_client = self.valid_registry()
        del missing_client["clients"][0]["display_name"]  # type: ignore[index]
        cases["missing client key"] = missing_client

        for label, data in cases.items():
            with self.subTest(label=label):
                self.write_registry(data)
                self.assert_registry_invalid()

    def test_registry_rejects_malformed_json_and_wrong_container_types(self) -> None:
        malformed_or_wrong = (
            "{",
            "[]",
            '{"schema_version": 1, "clients": {}}',
        )

        for content in malformed_or_wrong:
            with self.subTest(content=content):
                self.registry_path.write_text(content, encoding="utf-8")
                self.assert_registry_invalid()

    def test_registry_requires_supported_integer_schema_version(self) -> None:
        for schema_version in (True, 1.0, 2, "1", None):
            with self.subTest(schema_version=schema_version):
                data = self.valid_registry()
                data["schema_version"] = schema_version
                self.write_registry(data)
                self.assert_registry_invalid()

    def test_registry_rejects_duplicate_client_ids(self) -> None:
        data = self.valid_registry()
        data["clients"].append(dict(data["clients"][0]))  # type: ignore[union-attr,index]
        self.write_registry(data)

        error = self.assert_registry_invalid()

        self.assertIn("sample-client", error.message)

    def test_registry_rejects_invalid_client_metadata(self) -> None:
        invalid_values = {
            "empty id": ("id", ""),
            "non-portable id": ("id", "Sample Client"),
            "empty display name": ("display_name", " "),
            "boolean level": ("level", True),
            "floating-point level": ("level", 1.0),
            "unknown level": ("level", 3),
            "unknown verification": ("verification", "runtime"),
            "level one wrong verification": ("verification", "structure-smoke"),
        }

        for label, (field, value) in invalid_values.items():
            with self.subTest(label=label):
                data = self.valid_registry()
                data["clients"][0][field] = value  # type: ignore[index]
                self.write_registry(data)
                self.assert_registry_invalid()

    def test_registry_rejects_non_portable_or_escaping_paths(self) -> None:
        invalid_paths = (
            "",
            ".",
            "..",
            "../outside",
            "nested/../outside",
            "/absolute",
            "C:/absolute",
            r"C:\absolute",
            r".sample\skills",
            "//server/share",
            "nested//skills",
            "nested/./skills",
        )

        for field in ("project_path", "user_path"):
            for value in invalid_paths:
                with self.subTest(field=field, value=value):
                    data = self.valid_registry()
                    data["clients"][0][field] = value  # type: ignore[index]
                    self.write_registry(data)
                    self.assert_registry_invalid()

    def test_registry_rejects_duplicate_json_object_keys(self) -> None:
        self.registry_path.write_text(
            '{"schema_version":1,"schema_version":1,"clients":[]}',
            encoding="utf-8",
        )

        self.assert_registry_invalid()


class ManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.source = Path(self.temp_dir.name) / "source"
        self.source.mkdir()

    def test_manifest_is_sorted_and_contains_literal_size_and_sha256(self) -> None:
        (self.source / "nested").mkdir()
        (self.source / "z.txt").write_text("beta", encoding="utf-8")
        (self.source / "nested" / "a.txt").write_text("alpha", encoding="utf-8")

        manifest = build_manifest(self.source)

        self.assertEqual(
            (
                ManifestEntry(
                    relative_path="nested/a.txt",
                    size=5,
                    sha256=(
                        "8ed3f6ad685b959ead7022518e1af76cd"
                        "816f8e8ec7ccdda1ed4018e8f2223f8"
                    ),
                ),
                ManifestEntry(
                    relative_path="z.txt",
                    size=4,
                    sha256=(
                        "f44e64e75f3948e9f73f8dfa94721c4c"
                        "e8cbb4f265c4790c702b2d41cfbf2753"
                    ),
                ),
            ),
            manifest,
        )

    def test_manifest_changes_when_file_content_changes(self) -> None:
        tracked = self.source / "tracked.txt"
        tracked.write_text("alpha", encoding="utf-8")
        before = build_manifest(self.source)

        tracked.write_text("gamma", encoding="utf-8")
        after = build_manifest(self.source)

        self.assertEqual(
            "8ed3f6ad685b959ead7022518e1af76cd"
            "816f8e8ec7ccdda1ed4018e8f2223f8",
            before[0].sha256,
        )
        self.assertEqual(
            "be9d587defa1f0c09ef49eb17e206983a"
            "5f8f8289e4281860bd0ee5a19592c67",
            after[0].sha256,
        )
        self.assertNotEqual(before, after)

    def test_manifest_rejects_file_replaced_between_lstat_and_open(self) -> None:
        tracked = self.source / "tracked.txt"
        tracked.write_text("original", encoding="utf-8")
        outside = Path(self.temp_dir.name) / "outside.txt"
        outside.write_text("external content must not be hashed", encoding="utf-8")
        replacement = Path(self.temp_dir.name) / "replacement-link"
        try:
            replacement.symlink_to(outside)
        except OSError:
            os.link(outside, replacement)

        original_open = Path.open
        state = {"replaced": False, "read_called": False}

        class TrackingReader:
            def __init__(self, wrapped: object) -> None:
                self.wrapped = wrapped

            def __enter__(self) -> TrackingReader:
                self.wrapped.__enter__()  # type: ignore[union-attr]
                return self

            def __exit__(self, *args: object) -> object:
                return self.wrapped.__exit__(*args)  # type: ignore[union-attr]

            def fileno(self) -> int:
                return self.wrapped.fileno()  # type: ignore[union-attr,no-any-return]

            def read(self, size: int = -1) -> bytes:
                state["read_called"] = True
                return self.wrapped.read(size)  # type: ignore[union-attr,no-any-return]

        def replace_then_open(
            path: Path,
            *args: object,
            **kwargs: object,
        ) -> TrackingReader:
            if path == tracked and not state["replaced"]:
                os.replace(replacement, tracked)
                state["replaced"] = True
            wrapped = original_open(path, *args, **kwargs)  # type: ignore[arg-type]
            return TrackingReader(wrapped)

        with mock.patch.object(Path, "open", new=replace_then_open):
            with self.assertRaises(DistributionError) as raised:
                build_manifest(self.source)

        self.assertEqual("SOURCE_INVALID", raised.exception.code)
        self.assertEqual(tracked, raised.exception.path)
        self.assertTrue(state["replaced"])
        self.assertFalse(
            state["read_called"],
            "replacement content must be rejected before the first read",
        )

    def test_manifest_rejects_file_changed_during_read(self) -> None:
        tracked = self.source / "tracked.txt"
        tracked.write_text("original", encoding="utf-8")
        original_open = Path.open
        state = {"mutated": False}

        class MutatingReader:
            def __init__(self, wrapped: object) -> None:
                self.wrapped = wrapped

            def __enter__(self) -> MutatingReader:
                self.wrapped.__enter__()  # type: ignore[union-attr]
                return self

            def __exit__(self, *args: object) -> object:
                return self.wrapped.__exit__(*args)  # type: ignore[union-attr]

            def fileno(self) -> int:
                return self.wrapped.fileno()  # type: ignore[union-attr,no-any-return]

            def read(self, size: int = -1) -> bytes:
                content = self.wrapped.read(size)  # type: ignore[union-attr]
                if content and not state["mutated"]:
                    with original_open(
                        tracked,
                        "w",
                        encoding="utf-8",
                    ) as mutation_file:
                        mutation_file.write("changed after read")
                    state["mutated"] = True
                return content  # type: ignore[no-any-return]

        def mutate_during_open(
            path: Path,
            *args: object,
            **kwargs: object,
        ) -> object:
            wrapped = original_open(path, *args, **kwargs)  # type: ignore[arg-type]
            if path == tracked:
                return MutatingReader(wrapped)
            return wrapped

        with mock.patch.object(Path, "open", new=mutate_during_open):
            with self.assertRaises(DistributionError) as raised:
                build_manifest(self.source)

        self.assertEqual("SOURCE_INVALID", raised.exception.code)
        self.assertEqual(tracked, raised.exception.path)
        self.assertTrue(state["mutated"])

    def test_manifest_rejects_missing_source_and_source_file(self) -> None:
        source_file = Path(self.temp_dir.name) / "source.txt"
        source_file.write_text("content", encoding="utf-8")

        for source in (Path(self.temp_dir.name) / "missing", source_file):
            with self.subTest(source=source):
                with self.assertRaises(DistributionError) as raised:
                    build_manifest(source)

                self.assertEqual("SOURCE_INVALID", raised.exception.code)
                self.assertEqual(source, raised.exception.path)

    def test_manifest_maps_source_metadata_oserror_to_policy_error(self) -> None:
        denied = PermissionError(13, "access denied", str(self.source))

        with mock.patch(
            "tools.distribution.os.lstat",
            side_effect=denied,
        ):
            with self.assertRaises(DistributionError) as raised:
                build_manifest(self.source)

        self.assertEqual("SOURCE_INVALID", raised.exception.code)
        self.assertEqual(self.source, raised.exception.path)

    def test_manifest_rejects_symlinked_source(self) -> None:
        link = Path(self.temp_dir.name) / "source-link"
        try:
            link.symlink_to(self.source, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"directory symlinks unavailable: {error}")

        with self.assertRaises(DistributionError) as raised:
            build_manifest(link)

        self.assertEqual("SOURCE_INVALID", raised.exception.code)
        self.assertEqual(link, raised.exception.path)

    def test_manifest_rejects_symlink_inside_source(self) -> None:
        target = Path(self.temp_dir.name) / "outside.txt"
        target.write_text("outside", encoding="utf-8")
        link = self.source / "linked.txt"
        try:
            link.symlink_to(target)
        except OSError as error:
            self.skipTest(f"file symlinks unavailable: {error}")

        with self.assertRaises(DistributionError) as raised:
            build_manifest(self.source)

        self.assertEqual("SOURCE_INVALID", raised.exception.code)
        self.assertEqual(link, raised.exception.path)

    @unittest.skipUnless(os.name == "nt", "junctions are Windows-specific")
    def test_manifest_rejects_junction_inside_source(self) -> None:
        outside = Path(self.temp_dir.name) / "outside"
        outside.mkdir()
        outside_file = outside / "external.txt"
        outside_file.write_text("must not be hashed", encoding="utf-8")
        junction = self.source / "junction"
        create_windows_junction(self, junction, outside)

        with self.assertRaises(DistributionError) as raised:
            build_manifest(self.source)

        self.assertEqual("SOURCE_INVALID", raised.exception.code)
        self.assertEqual(junction, raised.exception.path)
        self.assertEqual("must not be hashed", outside_file.read_text(encoding="utf-8"))

    @unittest.skipUnless(os.name == "nt", "junctions are Windows-specific")
    def test_manifest_rejects_junction_as_source_root(self) -> None:
        outside = Path(self.temp_dir.name) / "outside-root"
        outside.mkdir()
        (outside / "external.txt").write_text("outside", encoding="utf-8")
        junction = Path(self.temp_dir.name) / "source-junction"
        create_windows_junction(self, junction, outside)

        with self.assertRaises(DistributionError) as raised:
            build_manifest(junction)

        self.assertEqual("SOURCE_INVALID", raised.exception.code)
        self.assertEqual(junction, raised.exception.path)

    @unittest.skipUnless(os.name == "nt", "junctions are Windows-specific")
    def test_manifest_rejects_directory_replaced_at_scandir_boundary(self) -> None:
        nested = self.source / "nested"
        nested.mkdir()
        (nested / "local.txt").write_text("local", encoding="utf-8")
        moved_nested = Path(self.temp_dir.name) / "verified-nested"
        outside = Path(self.temp_dir.name) / "outside-directory"
        outside.mkdir()
        external = outside / "external.txt"
        external.write_text("must not be hashed", encoding="utf-8")

        original_scandir = os.scandir
        original_open = Path.open
        state = {
            "swapped": False,
            "external_opened": False,
        }

        def swap_before_scandir(path: object) -> object:
            directory = Path(path)  # type: ignore[arg-type]
            if directory == nested and not state["swapped"]:
                os.replace(nested, moved_nested)
                create_windows_junction(self, nested, outside)
                state["swapped"] = True
            return original_scandir(path)  # type: ignore[arg-type]

        def track_external_open(
            path: Path,
            *args: object,
            **kwargs: object,
        ) -> object:
            if path == nested / external.name:
                state["external_opened"] = True
            return original_open(path, *args, **kwargs)  # type: ignore[arg-type]

        raised: DistributionError | None = None
        manifest: tuple[ManifestEntry, ...] | None = None
        with (
            mock.patch(
                "tools.distribution.os.scandir",
                side_effect=swap_before_scandir,
            ),
            mock.patch.object(Path, "open", new=track_external_open),
        ):
            try:
                manifest = build_manifest(self.source)
            except DistributionError as error:
                raised = error

        self.assertIsNotNone(
            raised,
            f"replaced directory was accepted: {manifest!r}",
        )
        self.assertEqual("SOURCE_INVALID", raised.code)  # type: ignore[union-attr]
        self.assertEqual(nested, raised.path)  # type: ignore[union-attr]
        self.assertTrue(state["swapped"])
        self.assertFalse(
            state["external_opened"],
            "external junction content must be rejected before hashing",
        )

    @unittest.skipIf(os.name == "nt", "FIFO files are not available on Windows")
    def test_manifest_rejects_non_regular_file(self) -> None:
        fifo = self.source / "pipe"
        os.mkfifo(fifo)

        with self.assertRaises(DistributionError) as raised:
            build_manifest(self.source)

        self.assertEqual("SOURCE_INVALID", raised.exception.code)
        self.assertEqual(fifo, raised.exception.path)


class TargetResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name) / "explicit-root"
        self.root.mkdir()
        self.client = ClientSpec(
            id="sample-client",
            display_name="Sample Client",
            level=1,
            project_path=".project/skills",
            user_path=".user/skills",
            verification="install-discovery",
        )

    def test_project_and_user_targets_append_the_canonical_skill_name(self) -> None:
        cases = {
            "project": self.root.resolve()
            / ".project"
            / "skills"
            / "tracing-spec-to-code",
            "user": self.root.resolve()
            / ".user"
            / "skills"
            / "tracing-spec-to-code",
        }

        for scope, expected in cases.items():
            with self.subTest(scope=scope):
                self.assertEqual(
                    expected,
                    resolve_install_target(self.client, scope, self.root),
                )

    def test_unknown_scope_and_non_directory_root_are_rejected(self) -> None:
        root_file = Path(self.temp_dir.name) / "root.txt"
        root_file.write_text("not a directory", encoding="utf-8")

        for scope, root in (
            ("workspace", self.root),
            ("project", root_file),
            ("user", Path(self.temp_dir.name) / "missing"),
        ):
            with self.subTest(scope=scope, root=root):
                with self.assertRaises(DistributionError) as raised:
                    resolve_install_target(self.client, scope, root)

                self.assertEqual("TARGET_INVALID", raised.exception.code)

    def test_root_resolve_runtime_error_maps_to_target_invalid(self) -> None:
        with mock.patch.object(
            Path,
            "resolve",
            side_effect=RuntimeError("symlink loop"),
        ):
            with self.assertRaises(DistributionError) as raised:
                resolve_install_target(self.client, "project", self.root)

        self.assertEqual("TARGET_INVALID", raised.exception.code)
        self.assertEqual(self.root, raised.exception.path)

    def test_candidate_resolve_oserror_maps_to_target_invalid(self) -> None:
        original_resolve = Path.resolve

        def fail_candidate(path: Path, strict: bool = False) -> Path:
            if strict:
                return original_resolve(path, strict=True)
            raise PermissionError(13, "access denied", str(path))

        with mock.patch.object(Path, "resolve", new=fail_candidate):
            with self.assertRaises(DistributionError) as raised:
                resolve_install_target(self.client, "project", self.root)

        expected_target = (
            self.root
            / ".project"
            / "skills"
            / "tracing-spec-to-code"
        )
        self.assertEqual("TARGET_INVALID", raised.exception.code)
        self.assertEqual(expected_target, raised.exception.path)

    def test_manually_constructed_unsafe_client_paths_are_rejected(self) -> None:
        unsafe_paths = (
            "../outside",
            "/absolute",
            "C:/absolute",
            r"C:\absolute",
            r".project\skills",
        )

        for unsafe_path in unsafe_paths:
            with self.subTest(path=unsafe_path):
                client = ClientSpec(
                    id="unsafe",
                    display_name="Unsafe",
                    level=1,
                    project_path=unsafe_path,
                    user_path=".user/skills",
                    verification="install-discovery",
                )

                with self.assertRaises(DistributionError) as raised:
                    resolve_install_target(client, "project", self.root)

                self.assertEqual("TARGET_INVALID", raised.exception.code)

    def test_existing_symlink_component_cannot_escape_explicit_root(self) -> None:
        outside = Path(self.temp_dir.name) / "outside"
        outside.mkdir()
        linked = self.root / "linked"
        try:
            linked.symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"directory symlinks unavailable: {error}")
        client = ClientSpec(
            id="unsafe",
            display_name="Unsafe",
            level=1,
            project_path="linked/skills",
            user_path=".user/skills",
            verification="install-discovery",
        )

        with self.assertRaises(DistributionError) as raised:
            resolve_install_target(client, "project", self.root)

        self.assertEqual("TARGET_INVALID", raised.exception.code)

    @unittest.skipUnless(os.name == "nt", "junctions are Windows-specific")
    def test_existing_junction_component_cannot_escape_explicit_root(self) -> None:
        outside = Path(self.temp_dir.name) / "outside-junction"
        outside.mkdir()
        junction = self.root / "linked"
        create_windows_junction(self, junction, outside)
        client = ClientSpec(
            id="unsafe",
            display_name="Unsafe",
            level=1,
            project_path="linked/skills",
            user_path=".user/skills",
            verification="install-discovery",
        )

        with self.assertRaises(DistributionError) as raised:
            resolve_install_target(client, "project", self.root)

        self.assertEqual("TARGET_INVALID", raised.exception.code)
        self.assertTrue(junction.is_dir())


class InstallationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.base = Path(self.temp_dir.name)
        self.source = self.base / "source"
        (self.source / "scripts").mkdir(parents=True)
        (self.source / "empty").mkdir()
        (self.source / "SKILL.md").write_bytes(b"# Controlled skill\n")
        (self.source / "scripts" / "run.py").write_bytes(
            b"print('controlled')\n"
        )
        self.client = ClientSpec(
            id="sample-client",
            display_name="Sample Client",
            level=1,
            project_path=".sample/project-skills",
            user_path=".sample/user-skills",
            verification="install-discovery",
        )

    def create_root(self, name: str = "root") -> Path:
        root = self.base / name
        root.mkdir()
        return root

    def assert_no_installer_workspace(self, target: Path) -> None:
        if not target.parent.exists():
            return
        leftovers = tuple(
            path.name
            for path in target.parent.iterdir()
            if path.name.startswith(".tracing-spec-to-code.tmp-")
        )
        self.assertEqual((), leftovers)

    def test_all_client_scope_combinations_install_complete_verified_copy(
        self,
    ) -> None:
        expected_paths = {
            ("codex", "project"): ".agents/skills",
            ("codex", "user"): ".agents/skills",
            ("claude-code", "project"): ".claude/skills",
            ("claude-code", "user"): ".claude/skills",
            ("github-copilot", "project"): ".github/skills",
            ("github-copilot", "user"): ".copilot/skills",
            ("antigravity", "project"): ".agent/skills",
            ("antigravity", "user"): ".gemini/antigravity/skills",
            ("gemini-cli", "project"): ".gemini/skills",
            ("gemini-cli", "user"): ".gemini/skills",
            ("cursor", "project"): ".cursor/skills",
            ("cursor", "user"): ".cursor/skills",
            ("windsurf", "project"): ".windsurf/skills",
            ("windsurf", "user"): ".codeium/windsurf/skills",
            ("cline", "project"): ".cline/skills",
            ("cline", "user"): ".cline/skills",
        }
        expected_manifest = (
            ManifestEntry(
                relative_path="SKILL.md",
                size=19,
                sha256=(
                    "a70fffbeb00f30b0c374b938b626075d"
                    "52382faaeaea37ee1ec04a57814255e6"
                ),
            ),
            ManifestEntry(
                relative_path="scripts/run.py",
                size=20,
                sha256=(
                    "52301911601556c1780394f15ae2ad6a"
                    "1d0a28df42b18ebcbce74612e136bca2"
                ),
            ),
        )

        for client in APPROVED_CLIENTS:
            for scope in ("project", "user"):
                with self.subTest(client=client.id, scope=scope):
                    root = self.create_root(f"{client.id}-{scope}")
                    result = install_skill(self.source, client, scope, root)
                    expected_target = (
                        root.resolve()
                        / expected_paths[(client.id, scope)]
                        / "tracing-spec-to-code"
                    )

                    self.assertEqual(
                        InstallResult(
                            client_id=client.id,
                            scope=scope,
                            target=expected_target,
                            file_count=2,
                        ),
                        result,
                    )
                    self.assertEqual(
                        expected_manifest,
                        build_manifest(result.target),
                    )
                    self.assertTrue((result.target / "empty").is_dir())
                    self.assert_no_installer_workspace(result.target)

    def test_skill_metadata_is_published_after_all_other_content(self) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        original_open = Path.open
        content_ready_when_metadata_opened: list[bool] = []

        def observe_metadata_publication(
            path: Path,
            mode: str = "r",
            *args: object,
            **kwargs: object,
        ):
            if path == target / "SKILL.md" and mode == "xb":
                content_ready_when_metadata_opened.append(
                    (target / "scripts" / "run.py").is_file()
                    and (target / "empty").is_dir()
                )
            return original_open(path, mode, *args, **kwargs)

        with mock.patch(
            "tools.distribution.Path.open",
            new=observe_metadata_publication,
        ):
            result = install_skill(
                self.source,
                self.client,
                "project",
                root,
            )

        self.assertEqual([True], content_ready_when_metadata_opened)
        self.assertEqual(
            ("SKILL.md", "scripts/run.py"),
            tuple(entry.relative_path for entry in build_manifest(result.target)),
        )

    def test_existing_target_preserves_sentinel_without_copying(self) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        target.mkdir(parents=True)
        sentinel = target / "sentinel.txt"
        sentinel.write_text("keep me", encoding="utf-8")

        with self.assertRaises(DistributionError) as raised:
            install_skill(self.source, self.client, "project", root)

        self.assertEqual("TARGET_EXISTS", raised.exception.code)
        self.assertEqual(target, raised.exception.path)
        self.assertEqual("keep me", sentinel.read_text(encoding="utf-8"))
        self.assertEqual(("sentinel.txt",), tuple(path.name for path in target.iterdir()))
        self.assert_no_installer_workspace(target)

    def test_source_preflight_failure_does_not_create_target(self) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        missing_source = self.base / "missing-source"

        with self.assertRaises(DistributionError) as raised:
            install_skill(missing_source, self.client, "project", root)

        self.assertEqual("SOURCE_INVALID", raised.exception.code)
        self.assertEqual(missing_source, raised.exception.path)
        self.assertFalse(os.path.lexists(target))
        self.assert_no_installer_workspace(target)

    def test_source_mutation_during_copy_is_rejected_before_publication(
        self,
    ) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        original_copy_tree_exclusive = (
            distribution_module._copy_tree_exclusive
        )

        def copy_then_mutate(
            source: Path,
            destination: Path,
            snapshot,
            destination_pin,
            owned_entries,
        ):
            result = original_copy_tree_exclusive(
                source,
                destination,
                snapshot,
                destination_pin,
                owned_entries,
            )
            if Path(source) == self.source:
                (self.source / "SKILL.md").write_bytes(
                    b"# Mutated source\n"
                )
            return result

        with mock.patch(
            "tools.distribution._copy_tree_exclusive",
            side_effect=copy_then_mutate,
        ):
            with self.assertRaises(DistributionError) as raised:
                install_skill(self.source, self.client, "project", root)

        self.assertEqual("SOURCE_INVALID", raised.exception.code)
        self.assertEqual(self.source, raised.exception.path)
        self.assertFalse(os.path.lexists(target))
        self.assert_no_installer_workspace(target)

    def test_partial_copy_failure_is_cleaned_and_mapped(self) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        original_open = Path.open
        staging_writes = 0

        def fail_second_staging_file(
            path: Path,
            mode: str = "r",
            *args: object,
            **kwargs: object,
        ) -> object:
            nonlocal staging_writes
            is_staging_path = any(
                parent.name.startswith(".tracing-spec-to-code.tmp-")
                for parent in path.parents
            )
            if is_staging_path and "x" in mode:
                staging_writes += 1
                if staging_writes == 2:
                    raise PermissionError(13, "copy denied", str(path))
            return original_open(path, mode, *args, **kwargs)

        with mock.patch.object(
            Path,
            "open",
            new=fail_second_staging_file,
        ):
            with self.assertRaises(DistributionError) as raised:
                install_skill(self.source, self.client, "project", root)

        self.assertEqual("COPY_FAILED", raised.exception.code)
        self.assertEqual(target, raised.exception.path)
        self.assertEqual(2, staging_writes)
        self.assertFalse(os.path.lexists(target))
        self.assert_no_installer_workspace(target)
        self.assertFalse((root / ".sample").exists())

    def test_missing_empty_directory_fails_staged_topology_verification(
        self,
    ) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        original_copy_tree_exclusive = (
            distribution_module._copy_tree_exclusive
        )

        def copy_then_remove_empty_directory(
            source: Path,
            destination: Path,
            snapshot,
            destination_pin,
            owned_entries,
        ):
            result = original_copy_tree_exclusive(
                source,
                destination,
                snapshot,
                destination_pin,
                owned_entries,
            )
            if Path(source) == self.source:
                os.rmdir(destination / "empty")
            return result

        with mock.patch(
            "tools.distribution._copy_tree_exclusive",
            side_effect=copy_then_remove_empty_directory,
        ):
            with self.assertRaises(DistributionError) as raised:
                install_skill(self.source, self.client, "project", root)

        self.assertEqual("VERIFY_FAILED", raised.exception.code)
        self.assertFalse(os.path.lexists(target))
        self.assert_no_installer_workspace(target)

    def test_extra_empty_directory_fails_staged_topology_verification(
        self,
    ) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        original_copy_tree_exclusive = (
            distribution_module._copy_tree_exclusive
        )
        added_directory: Path | None = None

        def copy_then_add_empty_directory(
            source: Path,
            destination: Path,
            snapshot,
            destination_pin,
            owned_entries,
        ):
            nonlocal added_directory
            result = original_copy_tree_exclusive(
                source,
                destination,
                snapshot,
                destination_pin,
                owned_entries,
            )
            if Path(source) == self.source:
                added_directory = destination / "unexpected-empty"
                added_directory.mkdir()
            return result

        with mock.patch(
            "tools.distribution._copy_tree_exclusive",
            side_effect=copy_then_add_empty_directory,
        ):
            with self.assertRaises(DistributionError) as raised:
                install_skill(self.source, self.client, "project", root)

        self.assertEqual("VERIFY_FAILED", raised.exception.code)
        self.assertIn("cleanup failed", raised.exception.message)
        self.assertFalse(os.path.lexists(target))
        self.assertIsNotNone(added_directory)
        self.assertTrue(added_directory.is_dir())  # type: ignore[union-attr]

    def test_staged_manifest_mismatch_is_cleaned_and_not_published(self) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        original_copy_tree_exclusive = (
            distribution_module._copy_tree_exclusive
        )

        def copy_then_corrupt(
            source: Path,
            destination: Path,
            snapshot,
            destination_pin,
            owned_entries,
        ):
            result = original_copy_tree_exclusive(
                source,
                destination,
                snapshot,
                destination_pin,
                owned_entries,
            )
            if Path(source) == self.source:
                (destination / "SKILL.md").write_bytes(b"corrupt")
            return result

        with mock.patch(
            "tools.distribution._copy_tree_exclusive",
            side_effect=copy_then_corrupt,
        ):
            with self.assertRaises(DistributionError) as raised:
                install_skill(self.source, self.client, "project", root)

        self.assertEqual("VERIFY_FAILED", raised.exception.code)
        self.assertEqual(target, raised.exception.path)
        self.assertFalse(os.path.lexists(target))
        self.assert_no_installer_workspace(target)

    def test_staged_replacement_is_preserved_as_not_owned(self) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        original_build_tree_snapshot = distribution_module._build_tree_snapshot
        replaced_file: Path | None = None

        def replace_before_staged_verification(
            source: Path,
            *,
            ignore_runtime_caches: bool = False,
        ):
            nonlocal replaced_file
            source_path = Path(source)
            if (
                source_path.name == "tracing-spec-to-code"
                and source_path.parent.name.startswith(
                    ".tracing-spec-to-code.tmp-"
                )
            ):
                replaced_file = source_path / "SKILL.md"
                replaced_file.unlink()
                replaced_file.write_bytes(b"external staged replacement")
            return original_build_tree_snapshot(
                source_path,
                ignore_runtime_caches=ignore_runtime_caches,
            )

        with mock.patch(
            "tools.distribution._build_tree_snapshot",
            side_effect=replace_before_staged_verification,
        ):
            with self.assertRaises(DistributionError) as raised:
                install_skill(self.source, self.client, "project", root)

        self.assertEqual("VERIFY_FAILED", raised.exception.code)
        self.assertIn("cleanup failed", raised.exception.message)
        self.assertIsNotNone(replaced_file)
        self.assertTrue(replaced_file.exists())  # type: ignore[union-attr]
        self.assertEqual(
            b"external staged replacement",
            replaced_file.read_bytes(),  # type: ignore[union-attr]
        )
        self.assertFalse(os.path.lexists(target))

    def test_publication_failure_is_cleaned_and_mapped(self) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        original_mkdir = os.mkdir

        def deny_target_claim(
            path: Path,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> None:
            if Path(path) == target:
                raise PermissionError(13, "publish denied", str(target))
            if dir_fd is None:
                original_mkdir(path, mode)
            else:
                original_mkdir(path, mode, dir_fd=dir_fd)

        with mock.patch("tools.distribution.os.mkdir", side_effect=deny_target_claim):
            with self.assertRaises(DistributionError) as raised:
                install_skill(self.source, self.client, "project", root)

        self.assertEqual("COPY_FAILED", raised.exception.code)
        self.assertEqual(target, raised.exception.path)
        self.assertFalse(os.path.lexists(target))
        self.assert_no_installer_workspace(target)

    def test_partial_publication_failure_removes_only_owned_target(self) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        unrelated = root / "unrelated.txt"
        unrelated.write_text("untouched", encoding="utf-8")
        original_open = Path.open
        publication_moves = 0

        def fail_second_publication_file(
            path: Path,
            mode: str = "r",
            *args: object,
            **kwargs: object,
        ) -> object:
            nonlocal publication_moves
            if path.is_relative_to(target) and "x" in mode:
                publication_moves += 1
                if publication_moves == 2:
                    raise PermissionError(
                        13,
                        "publication denied",
                        str(path),
                    )
            return original_open(path, mode, *args, **kwargs)

        with mock.patch.object(
            Path,
            "open",
            new=fail_second_publication_file,
        ):
            with self.assertRaises(DistributionError) as raised:
                install_skill(self.source, self.client, "project", root)

        self.assertEqual("COPY_FAILED", raised.exception.code)
        self.assertEqual(target, raised.exception.path)
        self.assertEqual(2, publication_moves)
        self.assertFalse(os.path.lexists(target))
        self.assertEqual("untouched", unrelated.read_text(encoding="utf-8"))
        self.assert_no_installer_workspace(target)

    def test_raced_child_file_is_not_overwritten(self) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        raced_file = target / "SKILL.md"
        original_open = Path.open

        def race_exclusive_file_creation(
            path: Path,
            mode: str = "r",
            *args: object,
            **kwargs: object,
        ) -> object:
            if path == raced_file and "x" in mode:
                with original_open(path, "wb") as file:
                    file.write(b"external race winner")
            return original_open(path, mode, *args, **kwargs)

        with mock.patch.object(
            Path,
            "open",
            new=race_exclusive_file_creation,
        ):
            with self.assertRaises(DistributionError) as raised:
                install_skill(self.source, self.client, "project", root)

        self.assertEqual("COPY_FAILED", raised.exception.code)
        self.assertIn("cleanup failed", raised.exception.message)
        self.assertEqual(b"external race winner", raced_file.read_bytes())

    @unittest.skipUnless(os.name == "nt", "junctions are Windows-specific")
    def test_deep_destination_junction_before_file_open_is_rejected(
        self,
    ) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        deep_directory = target / "scripts"
        moved_directory = target / "verified-scripts"
        outside = self.base / "deep-publication-outside"
        outside.mkdir()
        outside_sentinel = outside / "sentinel.txt"
        outside_sentinel.write_text("outside", encoding="utf-8")
        outside_file = outside / "run.py"
        destination_file = deep_directory / "run.py"
        original_open = Path.open
        diverted = False

        def divert_deep_directory_before_open(
            path: Path,
            mode: str = "r",
            *args: object,
            **kwargs: object,
        ) -> object:
            nonlocal diverted
            if path == destination_file and "x" in mode and not diverted:
                os.rename(deep_directory, moved_directory)
                create_windows_junction(self, deep_directory, outside)
                diverted = True
            return original_open(path, mode, *args, **kwargs)

        with mock.patch.object(
            Path,
            "open",
            new=divert_deep_directory_before_open,
        ):
            with self.assertRaises(DistributionError):
                install_skill(self.source, self.client, "project", root)

        self.assertTrue(diverted)
        self.assertFalse(outside_file.exists())
        self.assertEqual(
            "outside",
            outside_sentinel.read_text(encoding="utf-8"),
        )

    def test_source_runtime_caches_are_not_distributed_or_counted(self) -> None:
        cache_directory = self.source / "__pycache__"
        cache_directory.mkdir()
        (cache_directory / "module.cpython-314.pyc").write_bytes(b"cache")
        (self.source / "scripts" / "legacy.pyc").write_bytes(b"legacy")
        (self.source / "optimized.pyo").write_bytes(b"optimized")
        root = self.create_root()

        result = install_skill(
            self.source,
            self.client,
            "project",
            root,
        )

        self.assertEqual(2, result.file_count)
        self.assertEqual(
            ("SKILL.md", "scripts/run.py"),
            tuple(entry.relative_path for entry in build_manifest(result.target)),
        )
        self.assertFalse((result.target / "__pycache__").exists())
        self.assertFalse((result.target / "scripts" / "legacy.pyc").exists())
        self.assertFalse((result.target / "optimized.pyo").exists())

    def test_raced_cache_in_staging_is_not_ignored_by_verification(self) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        original_copy_tree_exclusive = (
            distribution_module._copy_tree_exclusive
        )

        def copy_then_add_cache(
            source: Path,
            destination: Path,
            snapshot,
            destination_pin,
            owned_entries,
        ):
            result = original_copy_tree_exclusive(
                source,
                destination,
                snapshot,
                destination_pin,
                owned_entries,
            )
            if Path(source) == self.source:
                raced_cache = destination / "__pycache__"
                raced_cache.mkdir()
                (raced_cache / "raced.pyc").write_bytes(b"raced")
            return result

        with mock.patch(
            "tools.distribution._copy_tree_exclusive",
            side_effect=copy_then_add_cache,
        ):
            with self.assertRaises(DistributionError) as raised:
                install_skill(self.source, self.client, "project", root)

        self.assertEqual("VERIFY_FAILED", raised.exception.code)
        self.assertFalse(os.path.lexists(target))

    def test_target_created_at_publication_boundary_is_preserved(self) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        sentinel = target / "sentinel.txt"
        original_mkdir = os.mkdir

        def race_target_claim(
            path: Path,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> None:
            if Path(path) == target:
                original_mkdir(path, mode)
                sentinel.write_text("race winner", encoding="utf-8")
                raise FileExistsError(17, "target appeared", str(target))
            if dir_fd is None:
                original_mkdir(path, mode)
            else:
                original_mkdir(path, mode, dir_fd=dir_fd)

        with mock.patch("tools.distribution.os.mkdir", side_effect=race_target_claim):
            with self.assertRaises(DistributionError) as raised:
                install_skill(self.source, self.client, "project", root)

        self.assertEqual("TARGET_EXISTS", raised.exception.code)
        self.assertEqual(target, raised.exception.path)
        self.assertEqual("race winner", sentinel.read_text(encoding="utf-8"))
        self.assert_no_installer_workspace(target)

    def test_empty_target_created_at_publication_boundary_is_not_replaced(
        self,
    ) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        original_mkdir = os.mkdir

        def race_empty_target_claim(
            path: Path,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> None:
            if Path(path) == target:
                original_mkdir(path, mode)
                raise FileExistsError(17, "empty target appeared", str(target))
            if dir_fd is None:
                original_mkdir(path, mode)
            else:
                original_mkdir(path, mode, dir_fd=dir_fd)

        with mock.patch(
            "tools.distribution.os.mkdir",
            side_effect=race_empty_target_claim,
        ):
            with self.assertRaises(DistributionError) as raised:
                install_skill(self.source, self.client, "project", root)

        self.assertEqual("TARGET_EXISTS", raised.exception.code)
        self.assertEqual(target, raised.exception.path)
        self.assertTrue(target.is_dir())
        self.assertEqual((), tuple(target.iterdir()))
        self.assert_no_installer_workspace(target)

    def test_final_verification_failure_removes_only_owned_target(self) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        unrelated = root / "unrelated.txt"
        unrelated.write_text("untouched", encoding="utf-8")
        original_build_manifest = build_manifest

        def corrupt_before_final_verification(
            source: Path,
        ) -> tuple[ManifestEntry, ...]:
            if Path(source) == target:
                (target / "SKILL.md").write_text(
                "corrupt after publication",
                encoding="utf-8",
            )
            return original_build_manifest(source)

        with mock.patch(
            "tools.distribution.build_manifest",
            side_effect=corrupt_before_final_verification,
        ):
            with self.assertRaises(DistributionError) as raised:
                install_skill(self.source, self.client, "project", root)

        self.assertEqual("VERIFY_FAILED", raised.exception.code)
        self.assertEqual(target, raised.exception.path)
        self.assertFalse(os.path.lexists(target))
        self.assertEqual("untouched", unrelated.read_text(encoding="utf-8"))
        self.assert_no_installer_workspace(target)

    def test_replacement_after_publication_is_preserved_as_not_owned(
        self,
    ) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        sentinel = target / "replacement.txt"
        original_build_manifest = build_manifest

        def replace_before_final_verification(
            source: Path,
        ) -> tuple[ManifestEntry, ...]:
            if Path(source) == target:
                shutil.rmtree(target)
                target.mkdir()
                sentinel.write_text("external replacement", encoding="utf-8")
            return original_build_manifest(source)

        with mock.patch(
            "tools.distribution.build_manifest",
            side_effect=replace_before_final_verification,
        ):
            with self.assertRaises(DistributionError) as raised:
                install_skill(self.source, self.client, "project", root)

        self.assertEqual("VERIFY_FAILED", raised.exception.code)
        self.assertEqual(target, raised.exception.path)
        self.assertIn("cleanup failed", raised.exception.message)
        self.assertEqual(
            "external replacement",
            sentinel.read_text(encoding="utf-8"),
        )
        self.assert_no_installer_workspace(target)

    def test_keyboard_interrupt_and_system_exit_are_not_policy_errors(
        self,
    ) -> None:
        for interruption in (KeyboardInterrupt(), SystemExit(9)):
            with self.subTest(interruption=type(interruption).__name__):
                root = self.create_root(type(interruption).__name__)
                target = resolve_install_target(
                    self.client,
                    "project",
                    root,
                )
                with mock.patch(
                    "tools.distribution._copy_tree_exclusive",
                    side_effect=interruption,
                ):
                    with self.assertRaises(type(interruption)) as raised:
                        install_skill(
                            self.source,
                            self.client,
                            "project",
                            root,
                        )

                if isinstance(interruption, SystemExit):
                    self.assertEqual(9, raised.exception.code)
                self.assertFalse(os.path.lexists(target))
                self.assert_no_installer_workspace(target)

    def test_cleanup_failure_does_not_replace_keyboard_interrupt(self) -> None:
        root = self.create_root()
        cleanup_failure = DistributionError(
            "COPY_FAILED",
            "simulated cleanup failure",
            root,
        )
        with (
            mock.patch(
                "tools.distribution._copy_tree_exclusive",
                side_effect=KeyboardInterrupt(),
            ),
            mock.patch(
                "tools.distribution._remove_owned_tree",
                side_effect=cleanup_failure,
            ),
        ):
            with self.assertRaises(KeyboardInterrupt) as raised:
                install_skill(
                    self.source,
                    self.client,
                    "project",
                    root,
                )

        notes = getattr(raised.exception, "__notes__", ())
        cleanup_attribute = getattr(
            raised.exception,
            "cleanup_failure",
            "",
        )
        self.assertTrue(
            any("cleanup failed" in note for note in notes)
            or "cleanup failed" in cleanup_attribute
        )

    @unittest.skipUnless(os.name == "nt", "junctions are Windows-specific")
    def test_cleanup_junction_preserves_original_error_and_outside(
        self,
    ) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        outside = self.base / "cleanup-outside"
        outside.mkdir()
        outside_sentinel = outside / "outside.txt"
        outside_sentinel.write_text("outside", encoding="utf-8")
        original_copy_tree_exclusive = (
            distribution_module._copy_tree_exclusive
        )
        injected_junction: Path | None = None

        def copy_corrupt_and_inject_junction(
            source: Path,
            destination: Path,
            snapshot,
            destination_pin,
            owned_entries,
        ):
            nonlocal injected_junction
            result = original_copy_tree_exclusive(
                source,
                destination,
                snapshot,
                destination_pin,
                owned_entries,
            )
            if Path(source) == self.source:
                (destination / "SKILL.md").write_bytes(b"corrupt")
                injected_junction = destination.parent / "injected-junction"
                create_windows_junction(
                    self,
                    injected_junction,
                    outside,
                )
            return result

        with mock.patch(
            "tools.distribution._copy_tree_exclusive",
            side_effect=copy_corrupt_and_inject_junction,
        ):
            with self.assertRaises(DistributionError) as raised:
                install_skill(self.source, self.client, "project", root)

        self.assertEqual("VERIFY_FAILED", raised.exception.code)
        self.assertIn("cleanup failed", raised.exception.message)
        self.assertIsNotNone(injected_junction)
        self.assertTrue(injected_junction.is_dir())  # type: ignore[union-attr]
        self.assertEqual(
            "outside",
            outside_sentinel.read_text(encoding="utf-8"),
        )
        self.assertFalse(os.path.lexists(target))

    @unittest.skipUnless(os.name == "nt", "junctions are Windows-specific")
    def test_parent_chain_creation_does_not_persist_outside_child(
        self,
    ) -> None:
        root = self.create_root()
        first_parent = root / ".sample"
        outside = self.base / "parent-chain-diversion"
        outside.mkdir()
        outside_child = outside / "project-skills"
        original_mkdir = os.mkdir
        diverted = False

        def divert_first_parent(
            path: Path,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> None:
            nonlocal diverted
            if Path(path) == first_parent and not diverted:
                create_windows_junction(self, first_parent, outside)
                diverted = True
                raise FileExistsError(17, "parent appeared", str(first_parent))
            if dir_fd is None:
                original_mkdir(path, mode)
            else:
                original_mkdir(path, mode, dir_fd=dir_fd)

        with mock.patch(
            "tools.distribution.os.mkdir",
            side_effect=divert_first_parent,
        ):
            with self.assertRaises(DistributionError) as raised:
                install_skill(
                    self.source,
                    self.client,
                    "project",
                    root,
                )

        self.assertEqual("TARGET_INVALID", raised.exception.code)
        self.assertTrue(diverted)
        self.assertFalse(outside_child.exists())

    def test_parent_chain_failure_removes_earlier_created_parents(self) -> None:
        root = self.create_root()
        first_parent = root / ".sample"
        failing_parent = first_parent / "project-skills"
        original_mkdir = os.mkdir

        def fail_later_parent(
            path: Path,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> None:
            if Path(path) == failing_parent:
                raise PermissionError(13, "simulated denial", str(path))
            if dir_fd is None:
                original_mkdir(path, mode)
            else:
                original_mkdir(path, mode, dir_fd=dir_fd)

        with mock.patch(
            "tools.distribution.os.mkdir",
            side_effect=fail_later_parent,
        ):
            with self.assertRaises(DistributionError) as raised:
                install_skill(
                    self.source,
                    self.client,
                    "project",
                    root,
                )

        self.assertEqual("COPY_FAILED", raised.exception.code)
        self.assertFalse(first_parent.exists())

    @unittest.skipUnless(os.name == "nt", "junctions are Windows-specific")
    def test_deeper_parent_junction_leaves_no_outside_child(self) -> None:
        root = self.create_root()
        first_parent = root / ".sample"
        first_parent.mkdir()
        moved_parent = root / "verified-parent"
        failing_parent = first_parent / "project-skills"
        outside = self.base / "deeper-parent-diversion"
        outside.mkdir()
        outside_child = outside / "project-skills"
        original_mkdir = os.mkdir
        diverted = False

        def divert_deeper_parent(
            path: Path,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> None:
            nonlocal diverted
            if Path(path) == failing_parent and not diverted:
                os.rename(first_parent, moved_parent)
                create_windows_junction(self, first_parent, outside)
                diverted = True
            if dir_fd is None:
                original_mkdir(path, mode)
            else:
                original_mkdir(path, mode, dir_fd=dir_fd)

        with mock.patch(
            "tools.distribution.os.mkdir",
            side_effect=divert_deeper_parent,
        ):
            with self.assertRaises(DistributionError) as raised:
                install_skill(
                    self.source,
                    self.client,
                    "project",
                    root,
                )

        self.assertEqual("TARGET_INVALID", raised.exception.code)
        self.assertTrue(diverted)
        self.assertFalse(outside_child.exists())

    @unittest.skipUnless(os.name == "nt", "junctions are Windows-specific")
    def test_parent_junction_replacement_at_workspace_boundary_is_rejected(
        self,
    ) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        target.parent.mkdir(parents=True)
        original_parent = target.parent
        moved_parent = original_parent.with_name("verified-parent")
        outside = self.base / "workspace-diversion"
        outside.mkdir()
        original_mkdtemp = tempfile.mkdtemp
        diverted = False

        def divert_before_workspace(*args: object, **kwargs: object) -> str:
            nonlocal diverted
            if not diverted:
                os.rename(original_parent, moved_parent)
                create_windows_junction(self, original_parent, outside)
                diverted = True
            return original_mkdtemp(*args, **kwargs)

        with mock.patch(
            "tools.distribution.tempfile.mkdtemp",
            side_effect=divert_before_workspace,
        ):
            with self.assertRaises(DistributionError) as raised:
                install_skill(self.source, self.client, "project", root)

        self.assertEqual("TARGET_INVALID", raised.exception.code)
        self.assertTrue(diverted)
        self.assertFalse((outside / "tracing-spec-to-code").exists())
        self.assertEqual(
            (),
            tuple(outside.glob(".tracing-spec-to-code.tmp-*")),
        )

    @unittest.skipUnless(os.name == "nt", "junctions are Windows-specific")
    def test_parent_junction_replacement_at_target_claim_is_rejected(
        self,
    ) -> None:
        root = self.create_root()
        target = resolve_install_target(self.client, "project", root)
        target.parent.mkdir(parents=True)
        original_parent = target.parent
        moved_parent = original_parent.with_name("verified-claim-parent")
        outside = self.base / "claim-diversion"
        outside.mkdir()
        original_mkdir = os.mkdir
        diverted = False

        def divert_target_claim(
            path: Path,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> None:
            nonlocal diverted
            if Path(path) == target and not diverted:
                os.rename(original_parent, moved_parent)
                create_windows_junction(self, original_parent, outside)
                diverted = True
            if dir_fd is None:
                original_mkdir(path, mode)
            else:
                original_mkdir(path, mode, dir_fd=dir_fd)

        with mock.patch(
            "tools.distribution.os.mkdir",
            side_effect=divert_target_claim,
        ):
            with self.assertRaises(DistributionError) as raised:
                install_skill(self.source, self.client, "project", root)

        self.assertEqual("TARGET_INVALID", raised.exception.code)
        self.assertTrue(diverted)
        self.assertFalse((outside / "tracing-spec-to-code").exists())


if __name__ == "__main__":
    unittest.main()
