#!/usr/bin/env python3
"""Mock-path tests for the Foundation v14 tooling-only smoke launcher."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
LAUNCHER = HERE / "smoke_openfoam14_tooling.sh"
REQUIRED_COMMANDS = ("foamVersion", "blockMesh", "checkMesh", "foamRun")
LOCKED_LAUNCH = r"""
set -eu
locked_path=$1
fake_bin=$2
launcher=$3
export PATH="$locked_path"
hash -r
[ "$PATH" = "$locked_path" ] || {
    printf '%s\n' 'MOCK_HARNESS_FAIL reason=path_lock_failed' >&2
    exit 97
}
printf '%s\n' "$PATH" > "$AJM_LOCKED_PATH_TRACE"
for command_name in foamVersion blockMesh checkMesh foamRun; do
    resolved="$(command -v "$command_name" 2>/dev/null || true)"
    expected="$fake_bin/$command_name"
    if [ -x "$expected" ]; then
        [ "$resolved" = "$expected" ] || {
            printf '%s\n' \
                "MOCK_HARNESS_FAIL reason=fake_resolution_failed command=$command_name" >&2
            exit 97
        }
    else
        [ -z "$resolved" ] || {
            printf '%s\n' \
                "MOCK_HARNESS_FAIL reason=unexpected_command_visible command=$command_name" >&2
            exit 97
        }
    fi
done
exec "$BASH" --noprofile --norc "$launcher"
"""


def find_bash() -> Path | None:
    candidate = (
        Path(r"C:\Program Files\Git\bin\bash.exe")
        if os.name == "nt"
        else Path("/bin/bash")
    )
    return candidate.resolve() if candidate.is_file() else None


class ToolingSmokeMockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bash = find_bash()
        if cls.bash is None:
            raise RuntimeError("required fixed bash unavailable")

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.fake_bin = self.root / "fake-bin"
        self.fake_bin.mkdir()
        self.tutorials = self.root / "tutorials"
        self.tutorials.mkdir()
        self.temp_root = self.root / "smoke-tmp"
        self.temp_root.mkdir()
        self.trace = self.root / "trace.txt"
        self.path_trace = self.root / "locked-path.txt"
        self.safe_path_dirs = self._safe_path_dirs()
        self._assert_no_real_openfoam_tools_in_safe_path()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _safe_path_dirs(self) -> list[Path]:
        if os.name == "nt":
            git_root = self.bash.parent.parent
            directories = [self.fake_bin, git_root / "usr" / "bin"]
        else:
            directories = [self.fake_bin, Path("/usr/bin"), Path("/bin")]
        for directory in directories:
            if not directory.is_dir():
                self.fail(f"required safe command directory unavailable: {directory}")
        return directories

    def _assert_no_real_openfoam_tools_in_safe_path(self) -> None:
        for directory in self.safe_path_dirs[1:]:
            for command in REQUIRED_COMMANDS:
                candidates = (directory / command, directory / f"{command}.exe")
                self.assertFalse(
                    any(candidate.exists() for candidate in candidates),
                    f"real OpenFOAM tool unexpectedly visible in mock PATH: {command}",
                )

    def _bash_path(self, path: Path) -> str:
        if os.name != "nt":
            return path.as_posix()
        resolved = path.resolve()
        rendered = resolved.as_posix()
        if len(rendered) < 3 or rendered[1:3] != ":/":
            self.fail(f"mock path is not on a Windows drive: {resolved}")
        return f"/{rendered[0].lower()}{rendered[2:]}"

    def _write_executable(self, name: str, body: str) -> None:
        path = self.fake_bin / name
        path.write_text("#!/usr/bin/env bash\nset -eu\n" + body, encoding="utf-8")
        path.chmod(0o755)

    def _install_fake_commands(
        self,
        *,
        omit: str | None = None,
        version: str = "OpenFOAM-14",
        version_exit: int = 0,
        run_reaches_end: bool = True,
        fail_stage: str | None = None,
    ) -> None:
        if omit != "foamVersion":
            self._write_executable(
                "foamVersion",
                f"printf '%s\\n' '{version}'\nexit {version_exit}\n",
            )
        for command in ("blockMesh", "checkMesh", "foamRun"):
            if omit == command:
                continue
            exit_code = 7 if fail_stage == command else 0
            output = ""
            if command == "foamRun":
                output = (
                    "printf 'End\\n'\n"
                    if run_reaches_end
                    else "printf 'solver stopped early\\n'\n"
                )
            self._write_executable(
                command,
                "printf '%s|%s|%s\\n' "
                f"'{command}' \"$PWD\" \"$*\" >> \"$AJM_FAKE_TRACE\"\n"
                f"{output}"
                f"exit {exit_code}\n",
            )

    def _make_tutorials(self, count: int) -> None:
        for index in range(count):
            case = self.tutorials / f"group-{index}" / "pitzDailySteady"
            case.mkdir(parents=True)
            (case / "SYNTHETIC_MOCK_ONLY").write_text(
                "not an OpenFOAM or AirJet case\n", encoding="utf-8"
            )

    def _environment(
        self,
        *,
        tutorials: Path | None = None,
        include_tutorials: bool = True,
    ) -> dict[str, str]:
        environment = {
            # The fixed Bash executable does not depend on this inherited value.
            # Git Bash rewrites it during startup, so LOCKED_LAUNCH replaces it
            # again before any launcher command can be resolved.
            "PATH": str(self.fake_bin),
            "TMPDIR": self._bash_path(self.temp_root),
            "AJM_FAKE_TRACE": self._bash_path(self.trace),
            "AJM_LOCKED_PATH_TRACE": self._bash_path(self.path_trace),
            "HOME": self._bash_path(self.root),
            "LC_ALL": "C",
        }
        if include_tutorials:
            environment["FOAM_TUTORIALS"] = self._bash_path(
                self.tutorials if tutorials is None else tutorials
            )
        return environment

    def _run(
        self,
        environment: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        locked_path = ":".join(
            self._bash_path(path) for path in self.safe_path_dirs
        )
        return subprocess.run(
            [
                str(self.bash),
                "--noprofile",
                "--norc",
                "-c",
                LOCKED_LAUNCH,
                "ajm-locked-launch",
                locked_path,
                self._bash_path(self.fake_bin),
                self._bash_path(LAUNCHER),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
            env=environment,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

    def _assert_path_was_locked(self) -> None:
        self.assertEqual(
            self.path_trace.read_text(encoding="utf-8").strip(),
            ":".join(self._bash_path(path) for path in self.safe_path_dirs),
        )

    def _assert_smoke_temp_clean(self) -> None:
        self.assertEqual(
            list(self.temp_root.glob("ajm-openfoam14-tooling.*")),
            [],
        )

    def test_bash_syntax_and_launcher_scope_are_frozen(self) -> None:
        result = subprocess.run(
            [
                str(self.bash),
                "--noprofile",
                "--norc",
                "-n",
                self._bash_path(LAUNCHER),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        source = LAUNCHER.read_text(encoding="utf-8")
        for token in (
            "OpenFOAM Foundation v14",
            "pitzDailySteady",
            "foamVersion",
            "blockMesh",
            "checkMesh",
            "foamRun",
            "mktemp -d",
            "trap 'rm -rf \"$smoke_root\"' EXIT",
            "cannot satisfy any P3-P6 gate",
            "reason=tempdir_creation_failed",
            "reason=tutorial_copy_failed",
            "reason=tutorial_copy_directory_invalid",
        ):
            self.assertIn(token, source)
        for forbidden in ("docker", "podman", "multipass", "wsl"):
            self.assertNotIn(forbidden, source.lower())
        self.assertNotIn("mapfile", source)

    def test_each_missing_required_command_fails_before_case_creation(self) -> None:
        self._make_tutorials(1)
        for command in REQUIRED_COMMANDS:
            with self.subTest(command=command):
                for child in self.fake_bin.iterdir():
                    child.unlink()
                self._install_fake_commands(omit=command)
                result = self._run(self._environment())
                self.assertEqual(result.returncode, 20)
                self.assertEqual(
                    result.stderr.strip(),
                    f"TOOLING_NOT_INSTALLED missing={command}",
                )
                self._assert_path_was_locked()
                self.assertFalse(self.trace.exists())
                self._assert_smoke_temp_clean()

    def test_version_and_environment_fail_closed_without_commands(self) -> None:
        self._make_tutorials(1)
        for version in (
            "OpenFOAM-v2312",
            "OpenFOAM-140",
            "vendor OpenFOAM-14 fake",
            "OpenFOAM 14",
        ):
            with self.subTest(version=version):
                for child in self.fake_bin.iterdir():
                    child.unlink()
                self._install_fake_commands(version=version)
                mismatch = self._run(self._environment())
                self.assertEqual(mismatch.returncode, 21)
                self.assertIn("TOOLING_VERSION_MISMATCH", mismatch.stderr)
                self._assert_path_was_locked()
                self.assertFalse(self.trace.exists())
                self._assert_smoke_temp_clean()

        for child in self.fake_bin.iterdir():
            child.unlink()
        self._install_fake_commands(version_exit=7)
        failed_version = self._run(self._environment())
        self.assertEqual(failed_version.returncode, 21)
        self.assertEqual(
            failed_version.stderr.strip(),
            "TOOLING_VERSION_MISMATCH "
            "reason=foamVersion_command_failed expected=OpenFOAM-14",
        )
        self._assert_path_was_locked()
        self.assertFalse(self.trace.exists())
        self._assert_smoke_temp_clean()

        for child in self.fake_bin.iterdir():
            child.unlink()
        self._install_fake_commands()
        unset = self._run(self._environment(include_tutorials=False))
        self.assertEqual(unset.returncode, 22)
        self.assertIn("FOAM_TUTORIALS=UNSET", unset.stderr)
        self.assertFalse(self.trace.exists())

        missing = self._run(
            self._environment(tutorials=self.root / "does-not-exist")
        )
        self.assertEqual(missing.returncode, 22)
        self.assertFalse(self.trace.exists())
        self._assert_smoke_temp_clean()

    def test_tempdir_failure_is_stable(self) -> None:
        self._make_tutorials(1)
        self._install_fake_commands()

        invalid_temp_root = self.root / "not-a-directory"
        invalid_temp_root.write_text("synthetic blocker\n", encoding="utf-8")
        temp_environment = self._environment()
        temp_environment["TMPDIR"] = self._bash_path(invalid_temp_root)
        temp_failure = self._run(temp_environment)
        self.assertEqual(temp_failure.returncode, 24)
        self.assertEqual(
            temp_failure.stderr.strip(),
            "TOOLING_SMOKE_FAIL reason=tempdir_creation_failed",
        )
        self.assertFalse(self.trace.exists())

    def test_tutorial_identity_requires_exactly_one_case(self) -> None:
        self._install_fake_commands()
        zero = self._run(self._environment())
        self.assertEqual(zero.returncode, 23)
        self.assertIn("count=0 expected=1", zero.stderr)
        self.assertFalse(self.trace.exists())

        self._make_tutorials(2)
        two = self._run(self._environment())
        self.assertEqual(two.returncode, 23)
        self.assertIn("count=2 expected=1", two.stderr)
        self.assertFalse(self.trace.exists())
        self._assert_smoke_temp_clean()

    def test_mock_success_orders_commands_isolates_copy_and_cleans(self) -> None:
        self._make_tutorials(1)
        self._install_fake_commands()
        result = self._run(self._environment())
        self.assertEqual(result.returncode, 0, result.stderr)
        self._assert_path_was_locked()
        self.assertEqual(
            result.stdout.strip(),
            "TOOLING_SMOKE_PASS case=pitzDailySteady version=OpenFOAM-14",
        )
        lines = self.trace.read_text(encoding="utf-8").splitlines()
        self.assertEqual(
            [line.split("|", 1)[0] for line in lines],
            ["blockMesh", "checkMesh", "foamRun"],
        )
        records = [line.split("|", 2) for line in lines]
        working_directories = [record[1] for record in records]
        self.assertEqual(len(set(working_directories)), 1)
        self.assertTrue(working_directories[0].endswith("/case"))
        self.assertTrue(
            working_directories[0].startswith(
                self._bash_path(self.temp_root)
                + "/ajm-openfoam14-tooling."
            )
        )
        self.assertEqual(
            [record[2] for record in records],
            ["", "-allGeometry -allTopology", ""],
        )
        self.assertTrue(
            (
                self.tutorials
                / "group-0"
                / "pitzDailySteady"
                / "SYNTHETIC_MOCK_ONLY"
            ).is_file()
        )
        self._assert_smoke_temp_clean()

    def test_solver_without_end_marker_is_stable_failure_and_cleans(self) -> None:
        self._make_tutorials(1)
        self._install_fake_commands(run_reaches_end=False)
        result = self._run(self._environment())
        self.assertEqual(result.returncode, 24)
        self.assertEqual(
            result.stderr.strip(),
            "TOOLING_SMOKE_FAIL reason=solver_did_not_reach_End",
        )
        self._assert_smoke_temp_clean()

    def test_each_mock_stage_failure_is_stable_and_cleans(self) -> None:
        self._make_tutorials(1)
        for stage in ("blockMesh", "checkMesh", "foamRun"):
            with self.subTest(stage=stage):
                for child in self.fake_bin.iterdir():
                    child.unlink()
                if self.trace.exists():
                    self.trace.unlink()
                self._install_fake_commands(fail_stage=stage)
                result = self._run(self._environment())
                self.assertEqual(result.returncode, 24, result.stderr)
                self.assertEqual(
                    result.stderr.strip(),
                    f"TOOLING_SMOKE_FAIL reason={stage}_command_failed",
                )
                self._assert_smoke_temp_clean()


if __name__ == "__main__":
    unittest.main(verbosity=2)
