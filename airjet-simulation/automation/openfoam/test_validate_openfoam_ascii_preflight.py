#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "validate_openfoam_ascii_preflight.py"
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
SPEC = importlib.util.spec_from_file_location("ascii_preflight", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
SAFE_IO = sys.modules[MODULE.read_bounded_regular_file.__module__]


def contract() -> dict[str, object]:
    return {
        "schema_version": "AJM_PLAN_B_OPENFOAM_ASCII_PREFLIGHT_V1",
        "openfoam_distribution": "OpenFOAM Foundation",
        "openfoam_major": 14,
        "case_scope": "P3_CELL_CALIBRATION_REFERENCE",
        "source_commit": "1" * 40,
        "geometry_manifest_sha256": "2" * 64,
        "patch_roles": {
            "inlet": ["inletA"],
            "outlet": ["outletA"],
            "jet": ["jetA"],
        },
        "chamber_cell_zone": "chamberCells",
        "fields": {
            "rho": {
                "object": "rho",
                "class": "volScalarField",
                "dimensions": [1, -3, 0, 0, 0, 0, 0],
            },
            "phi": {
                "object": "phi",
                "class": "surfaceScalarField",
                "dimensions": [1, 0, -1, 0, 0, 0, 0],
            },
            "p": {
                "object": "p",
                "class": "volScalarField",
                "dimensions": [1, -1, -2, 0, 0, 0, 0],
            },
            "U": {
                "object": "U",
                "class": "volVectorField",
                "dimensions": [0, 1, -1, 0, 0, 0, 0],
            },
        },
    }


def header(class_name: str, object_name: str, format_name: str = "ascii") -> str:
    return f"""FoamFile
{{
    version 2.0;
    format {format_name};
    class {class_name};
    object {object_name};
}}
"""


def boundary() -> str:
    return header("polyBoundaryMesh", "boundary") + """3
(
inletA { type patch; nFaces 2; startFace 10; }
outletA { type patch; nFaces 3; startFace 12; }
jetA { type patch; nFaces 4; startFace 15; }
)
"""


def zones() -> str:
    return header("regIOobject", "cellZones") + """1
(
chamberCells
{
    type cellZone;
    cellLabels List<label> 3(0 2 4);
}
)
"""


def field(name: str, class_name: str, dimensions: list[int]) -> str:
    dims = " ".join(str(value) for value in dimensions)
    return header(class_name, name) + f"""dimensions [{dims}];
internalField uniform 0;
boundaryField
{{
    inletA {{ type zeroGradient; }}
}}
"""


class PreflightTests(unittest.TestCase):
    def make_case(
        self,
        root: Path,
        contract_value: dict[str, object] | None = None,
        boundary_text: str | None = None,
        zone_text: str | None = None,
    ) -> tuple[Path, Path, Path, dict[str, Path]]:
        value = contract() if contract_value is None else contract_value
        contract_path = root / "contract.json"
        contract_path.write_text(json.dumps(value), encoding="utf-8")
        boundary_path = root / "boundary"
        boundary_path.write_text(
            boundary() if boundary_text is None else boundary_text, encoding="utf-8"
        )
        zones_path = root / "cellZones"
        zones_path.write_text(
            zones() if zone_text is None else zone_text, encoding="utf-8"
        )
        fields: dict[str, Path] = {}
        for role, spec in value["fields"].items():  # type: ignore[union-attr]
            path = root / f"field-{role}"
            path.write_text(
                field(spec["object"], spec["class"], spec["dimensions"]),  # type: ignore[index]
                encoding="utf-8",
            )
            fields[role] = path
        return contract_path, boundary_path, zones_path, fields

    def run_case(
        self,
        paths: tuple[Path, Path, Path, dict[str, Path]],
        reverse_fields: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        contract_path, boundary_path, zones_path, fields = paths
        roles = sorted(fields, reverse=reverse_fields)
        command = [
            sys.executable,
            str(SCRIPT),
            "--contract",
            str(contract_path),
            "--boundary",
            str(boundary_path),
            "--cell-zones",
            str(zones_path),
        ]
        for role in roles:
            command.extend(["--field", f"{role}={fields[role]}"])
        return subprocess.run(
            command, check=False, capture_output=True, text=True, timeout=10
        )

    def test_valid_case_is_deterministic_and_conservative(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            paths = self.make_case(Path(raw))
            first = self.run_case(paths)
            second = self.run_case(paths, reverse_fields=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        result = json.loads(first.stdout)
        self.assertEqual(result["status"], "CASE_SOURCE_PREFLIGHT_ACCEPTED")
        self.assertEqual(result["boundary"]["patch_count"], 3)
        self.assertEqual(result["boundary"]["total_boundary_faces"], 9)
        self.assertEqual(result["cell_zones"]["chamber_cell_count"], 3)
        self.assertTrue(result["required_ascii_metadata_verified"])
        self.assertTrue(result["role_poly_patch_types_verified"])
        self.assertTrue(result["required_export_field_semantics_verified"])
        self.assertFalse(result["complete_openfoam_grammar_verified"])
        self.assertFalse(result["cross_file_snapshot_atomic"])
        for key in (
            "boundary_condition_physics_verified",
            "mesh_owner_neighbour_verified",
            "mesh_geometry_quality_verified",
            "cell_zone_mesh_membership_verified",
            "runtime_verified",
            "solver_verified",
            "solver_authorized",
        ):
            self.assertFalse(result[key])
        self.assertEqual(result["formal_gate_effect"], "NONE")
        self.assertNotIn(str(paths[0].parent), first.stdout)

    def test_boundary_count_zero_face_and_range_errors_reject(self) -> None:
        cases = (
            (boundary().replace("3\n(", "4\n(", 1), "BOUNDARY_DECLARED_COUNT"),
            (boundary().replace("nFaces 2", "nFaces 0"), "BOUNDARY_ZERO_FACE"),
            (boundary().replace("startFace 12", "startFace 13"), "BOUNDARY_FACE_RANGES"),
            (boundary().replace("outletA", "inletA"), "BOUNDARY_PATCH_NAME"),
            (
                boundary().replace("inletA { type patch", "inletA { type empty"),
                "BOUNDARY_ROLE_POLYPATCH_TYPE_INVALID",
            ),
        )
        for text, code in cases:
            with self.subTest(code=code), tempfile.TemporaryDirectory() as raw:
                result = self.run_case(
                    self.make_case(Path(raw), boundary_text=text)
                )
            self.assertEqual(result.returncode, 2)
            self.assertIn(code, result.stderr)

    def test_required_role_patch_and_contract_overlap_reject(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            value = contract()
            value["patch_roles"]["inlet"] = ["missing"]  # type: ignore[index]
            result = self.run_case(self.make_case(Path(raw), value))
        self.assertEqual(result.returncode, 2)
        self.assertIn("BOUNDARY_REQUIRED_ROLE_PATCH_MISSING", result.stderr)

        with tempfile.TemporaryDirectory() as raw:
            value = contract()
            value["patch_roles"]["jet"] = ["inletA"]  # type: ignore[index]
            result = self.run_case(self.make_case(Path(raw), value))
        self.assertEqual(result.returncode, 2)
        self.assertIn("CONTRACT_PATCH_ROLES_OVERLAP", result.stderr)

    def test_cellzone_count_missing_empty_and_duplicate_labels_reject(self) -> None:
        cases = (
            (zones().replace("1\n(", "2\n(", 1), "CELLZONE_DECLARED_COUNT"),
            (zones().replace("chamberCells", "otherCells"), "CHAMBER_CELLZONE_MISSING"),
            (zones().replace("3(0 2 4)", "0()"), "CELLZONE_LABEL_COUNT_MISMATCH"),
            (zones().replace("3(0 2 4)", "3(0 2 2)"), "CELLZONE_LABEL_DUPLICATE"),
        )
        for text, code in cases:
            with self.subTest(code=code), tempfile.TemporaryDirectory() as raw:
                result = self.run_case(self.make_case(Path(raw), zone_text=text))
            self.assertEqual(result.returncode, 2)
            self.assertIn(code, result.stderr)

    def test_field_header_and_dimensions_reject(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            paths = self.make_case(Path(raw))
            paths[3]["p"].write_text(
                field("p", "volScalarField", [0, 2, -2, 0, 0, 0, 0]),
                encoding="utf-8",
            )
            result = self.run_case(paths)
        self.assertEqual(result.returncode, 2)
        self.assertIn("FIELD_DIMENSIONS_MISMATCH", result.stderr)

        with tempfile.TemporaryDirectory() as raw:
            paths = self.make_case(Path(raw))
            paths[3]["U"].write_text(
                field("wrong", "volVectorField", [0, 1, -1, 0, 0, 0, 0]),
                encoding="utf-8",
            )
            result = self.run_case(paths)
        self.assertEqual(result.returncode, 2)
        self.assertIn("FOAM_HEADER_OBJECT_MISMATCH", result.stderr)

        with tempfile.TemporaryDirectory() as raw:
            paths = self.make_case(Path(raw))
            paths[3]["rho"].write_text(
                field("rho", "volScalarField", [1, -3, 0, 0, 0, 0, 0]) + "(\n",
                encoding="utf-8",
            )
            result = self.run_case(paths)
        self.assertEqual(result.returncode, 2)
        self.assertIn("FIELD_DELIMITERS_UNBALANCED", result.stderr)

        misleading = field(
            "rho", "volScalarField", [1, -3, 0, 0, 0, 0, 0]
        ).replace(
            "dimensions [1 -3 0 0 0 0 0];",
            "junk dimensions [1 -3 0 0 0 0 0];",
        )
        with tempfile.TemporaryDirectory() as raw:
            paths = self.make_case(Path(raw))
            paths[3]["rho"].write_text(misleading, encoding="utf-8")
            result = self.run_case(paths)
        self.assertEqual(result.returncode, 2)
        self.assertIn("FIELD_DIMENSIONS_MISSING", result.stderr)

        misleading_paren = field(
            "rho", "volScalarField", [1, -3, 0, 0, 0, 0, 0]
        ).replace(
            "dimensions [1 -3 0 0 0 0 0];",
            "junk ( dimensions [1 -3 0 0 0 0 0]; );",
        )
        with tempfile.TemporaryDirectory() as raw:
            paths = self.make_case(Path(raw))
            paths[3]["rho"].write_text(misleading_paren, encoding="utf-8")
            result = self.run_case(paths)
        self.assertEqual(result.returncode, 2)
        self.assertIn("FIELD_DIMENSIONS_MISSING", result.stderr)

    def test_binary_directive_macro_and_trailing_tokens_reject(self) -> None:
        cases = (
            (boundary().replace("format ascii", "format binary"), "FOAM_FORMAT_NOT_ASCII"),
            (boundary() + "#include \"x\"\n", "FOAM_DIRECTIVE_OR_MACRO"),
            (boundary() + "$x\n", "FOAM_DIRECTIVE_OR_MACRO"),
            (boundary() + "junk\n", "FOAM_TRAILING_TOKENS"),
        )
        for text, code in cases:
            with self.subTest(code=code), tempfile.TemporaryDirectory() as raw:
                result = self.run_case(
                    self.make_case(Path(raw), boundary_text=text)
                )
            self.assertEqual(result.returncode, 2)
            self.assertIn(code, result.stderr)

    def test_comments_are_supported_but_unterminated_comment_rejects(self) -> None:
        valid = boundary().replace("3\n(", "/* patches */\n3\n(", 1)
        with tempfile.TemporaryDirectory() as raw:
            result = self.run_case(self.make_case(Path(raw), boundary_text=valid))
        self.assertEqual(result.returncode, 0, result.stderr)
        with tempfile.TemporaryDirectory() as raw:
            result = self.run_case(
                self.make_case(Path(raw), boundary_text=boundary() + "/*")
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("FOAM_UNTERMINATED_COMMENT", result.stderr)

    def test_contract_duplicate_extra_deep_and_float_reject(self) -> None:
        raw_contracts = (
            ('{"schema_version":"a","schema_version":"b"}', "DUPLICATE_JSON_KEY"),
            (json.dumps({**contract(), "extra": 1}), "CONTRACT_KEYS_MISMATCH"),
            ("[" * 100 + "0" + "]" * 100, "JSON_DEPTH_LIMIT_EXCEEDED"),
            ('{"value":1.0}', "JSON_FLOAT_REJECTED"),
        )
        for text, code in raw_contracts:
            with self.subTest(code=code), tempfile.TemporaryDirectory() as raw:
                paths = self.make_case(Path(raw))
                paths[0].write_text(text, encoding="utf-8")
                result = self.run_case(paths)
            self.assertEqual(result.returncode, 2)
            self.assertIn(code, result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_contract_requires_exact_export_field_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            value = contract()
            value["fields"] = {
                "temperature": {
                    "object": "T",
                    "class": "volScalarField",
                    "dimensions": [0, 0, 0, 1, 0, 0, 0],
                }
            }
            paths = self.make_case(Path(raw), value)
            result = self.run_case(paths)
        self.assertEqual(result.returncode, 2)
        self.assertIn("CONTRACT_FIELDS_INVALID", result.stderr)

        with tempfile.TemporaryDirectory() as raw:
            value = contract()
            value["fields"]["phi"]["dimensions"] = [0, 3, -1, 0, 0, 0, 0]  # type: ignore[index]
            paths = self.make_case(Path(raw), value)
            result = self.run_case(paths)
        self.assertEqual(result.returncode, 2)
        self.assertIn("CONTRACT_EXPORT_FIELD_SEMANTICS_MISMATCH", result.stderr)

    def test_dictionary_closing_brace_cannot_be_value_data(self) -> None:
        broken = boundary().replace(
            "type patch; nFaces 2; startFace 10;",
            "type patch; nFaces 2; startFace 10; junk x } ;",
        )
        with tempfile.TemporaryDirectory() as raw:
            result = self.run_case(
                self.make_case(Path(raw), boundary_text=broken)
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("FOAM_DICTIONARY_VALUE_UNTERMINATED", result.stderr)

    def test_field_argument_role_mismatch_and_duplicate_reject(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            paths = self.make_case(Path(raw))
            command = [
                sys.executable,
                str(SCRIPT),
                "--contract",
                str(paths[0]),
                "--boundary",
                str(paths[1]),
                "--cell-zones",
                str(paths[2]),
                "--field",
                f"rho={paths[3]['rho']}",
            ]
            result = subprocess.run(
                command, check=False, capture_output=True, text=True, timeout=10
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("FIELD_ARGUMENT_ROLES_MISMATCH", result.stderr)

    def test_missing_nul_bom_non_utf8_and_oversize_reject(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            paths = self.make_case(Path(raw))
            paths[1].unlink()
            result = self.run_case(paths)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, "REJECTED: INPUT_SAFE_READ_REJECTED\n")
        self.assertNotIn("Traceback", result.stderr)

        for data, code in (
            (b"\x00", "INPUT_NUL_REJECTED"),
            (b"\xef\xbb\xbf" + boundary().encode(), "INPUT_UTF8_BOM_REJECTED"),
            (b"\xff", "INPUT_NOT_UTF8"),
            (b"x" * (MODULE.MAX_FOAM_BYTES + 1), "INPUT_SAFE_READ_REJECTED"),
        ):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as raw:
                paths = self.make_case(Path(raw))
                paths[1].write_bytes(data)
                result = self.run_case(paths)
            self.assertEqual(result.returncode, 2)
            self.assertIn(code, result.stderr)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink unavailable")
    def test_symlink_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self.make_case(root)
            link = root / "boundary-link"
            try:
                link.symlink_to(paths[1])
            except OSError as exc:
                self.skipTest(f"symlink privilege unavailable: {exc}")
            result = self.run_case((paths[0], link, paths[2], paths[3]))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, "REJECTED: INPUT_SAFE_READ_REJECTED\n")

    def test_shared_reader_errors_are_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "input"
            path.write_text("x", encoding="utf-8")
            for shared_code in (
                "ARTIFACT_IDENTITY_DRIFT",
                "ARTIFACT_READ_REJECTED",
            ):
                with self.subTest(shared_code=shared_code), mock.patch.object(
                    MODULE,
                    "read_bounded_regular_file",
                    side_effect=MODULE.SafeArtifactError(shared_code),
                ):
                    with self.assertRaisesRegex(
                        MODULE.PreflightError, "^INPUT_SAFE_READ_REJECTED$"
                    ):
                        MODULE.read_stable(path, 100)

    def test_shared_reader_enforces_final_path_and_double_read_identity(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "input"
            path.write_text("x", encoding="utf-8")

            actual_path = str(path.resolve())
            with mock.patch.object(
                SAFE_IO,
                "_handle_final_path",
                side_effect=(actual_path, actual_path + "-alias"),
            ) as final_path:
                with self.assertRaisesRegex(
                    MODULE.PreflightError, "^INPUT_SAFE_READ_REJECTED$"
                ):
                    MODULE.read_stable(path, 100)
            self.assertEqual(final_path.call_count, 2)

            actual_read = SAFE_IO._read_fd_bytes
            read_count = 0

            def drift_on_second_read(
                descriptor: int, maximum: int, code: str
            ) -> bytes:
                nonlocal read_count
                data = actual_read(descriptor, maximum, code)
                read_count += 1
                return data if read_count == 1 else data + b"!"

            with mock.patch.object(
                SAFE_IO, "_read_fd_bytes", side_effect=drift_on_second_read
            ):
                with self.assertRaisesRegex(
                    MODULE.PreflightError, "^INPUT_SAFE_READ_REJECTED$"
                ):
                    MODULE.read_stable(path, 100)
            self.assertEqual(read_count, 2)

    def test_hardlink_input_is_rejected_by_shared_reader(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self.make_case(root)
            alias = root / "boundary-hardlink"
            try:
                os.link(paths[1], alias)
            except OSError as exc:
                self.skipTest(f"hardlink unavailable: {exc}")
            result = self.run_case((paths[0], alias, paths[2], paths[3]))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, "REJECTED: INPUT_SAFE_READ_REJECTED\n")

    def test_shared_reader_adapter_preserves_stable_input_and_nul_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "input"
            path.write_bytes(b"abc")
            stable = MODULE.read_stable(path, 100)
            self.assertEqual(stable.data, b"abc")
            self.assertEqual(
                stable.sha256,
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            )
            path.write_bytes(b"a\x00b")
            with self.assertRaisesRegex(
                MODULE.PreflightError, "^INPUT_NUL_REJECTED$"
            ):
                MODULE.read_stable(path, 100)

    def test_source_has_no_process_network_or_write_api(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for token in (
            "import subprocess",
            "from subprocess",
            "import socket",
            "from socket",
            "requests",
            "urllib",
            "os.system",
            "os.open(",
            "os.read(",
            "os.fstat(",
            "os.lstat(",
            "Popen(",
            "write_text(",
            "write_bytes(",
            "open(\"w",
        ):
            with self.subTest(token=token):
                self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
