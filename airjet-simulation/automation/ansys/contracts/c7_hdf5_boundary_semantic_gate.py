#!/usr/bin/env python3
"""Read-only C7 Fluent HDF5 boundary-semantic gate.

The semantic validator is independent of Fluent and third-party Python
packages.  The optional HDF5 extractor invokes the read-only ``h5dump``
utility with a fixed argument vocabulary; it never starts an ANSYS engine.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


PASS_STATUS = "MAIN_VOLUME_PASS_BOUNDARY_SEMANTICS_PASS"
FAIL_STATUS = "MAIN_VOLUME_PASS_BOUNDARY_SEMANTICS_FAIL"
FORMAT_VERSION = "26.1"
SOLVER_MARKER = "ANSYS_FLUENT_MESHING"
CELL_ZONE_NAME = "ajm006_v03_fluid_continuous"
INTERIOR_NAME = "interior--ajm006_v03_fluid_continuous"
CANONICAL_BOUNDARIES = {
    "ajm006_v03_inlet_01": 10,
    "ajm006_v03_inlet_02": 10,
    "ajm006_v03_inlet_03": 10,
    "ajm006_v03_inlet_04": 10,
    "ajm006_v03_outlet": 5,
    "ajm006_v03_heat_wall": 3,
    "ajm006_v03_membrane_top": 3,
    "ajm006_v03_membrane_bottom": 3,
    "ajm006_v03_orifice_throat_wall": 3,
    "ajm006_v03_remaining_wall": 3,
}
EXPECTED_BBOX_MIN_MM = (-10.875, -17.750025, 1.2675)
EXPECTED_BBOX_MAX_MM = (10.89, 20.75, 2.800025)
BBOX_TOLERANCE_MM = 0.02
STUDENT_ENTITY_LIMIT = 1_000_000


class GateError(RuntimeError):
    pass


def _error(errors: List[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _valid_int(value: Any) -> bool:
    return type(value) is int


def _ranges_are_contiguous(rows: Sequence[Dict[str, Any]]) -> bool:
    expected = 1
    for row in sorted(rows, key=lambda item: item.get("min_id", -1)):
        low, high = row.get("min_id"), row.get("max_id")
        if not _valid_int(low) or not _valid_int(high) or low != expected or high < low:
            return False
        expected = high + 1
    return True


def validate_observation(observation: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a normalized observation and return a deterministic verdict."""
    errors: List[str] = []
    if observation.get("format_version") != FORMAT_VERSION:
        _error(errors, "C7_HDF5_VERSION_INVALID")
    if observation.get("solver") != SOLVER_MARKER:
        _error(errors, "C7_HDF5_SOLVER_MARKER_INVALID")

    cells = observation.get("cell_zones")
    if not isinstance(cells, list) or len(cells) != 1:
        _error(errors, "C7_CELL_ZONE_NOT_UNIQUE")
        cells = []
    if cells:
        cell = cells[0]
        if cell.get("name") != CELL_ZONE_NAME:
            _error(errors, "C7_CELL_ZONE_NAME_INVALID")
        if not _ranges_are_contiguous(cells):
            _error(errors, "C7_CELL_RANGE_INVALID")
        derived_cell_count = cell.get("max_id", 0) - cell.get("min_id", 1) + 1
        if (
            not _valid_int(observation.get("cell_count"))
            or observation["cell_count"] != derived_cell_count
            or not 0 < derived_cell_count < STUDENT_ENTITY_LIMIT
        ):
            _error(errors, "C7_CELL_COUNT_INVALID")

    faces = observation.get("face_zones")
    if not isinstance(faces, list):
        _error(errors, "C7_FACE_ZONE_TABLE_INVALID")
        faces = []
    names = [row.get("name") for row in faces if isinstance(row, dict)]
    expected_names = {INTERIOR_NAME} | set(CANONICAL_BOUNDARIES)
    if len(names) != len(set(names)):
        _error(errors, "C7_FACE_ZONE_NAME_DUPLICATE")
    if set(names) != expected_names or len(faces) != 11:
        _error(errors, "C7_CANONICAL_10_ZONE_INVENTORY_INVALID")
    if not _ranges_are_contiguous(faces):
        _error(errors, "C7_FACE_RANGE_INVALID")
    for row in faces:
        if not isinstance(row, dict):
            _error(errors, "C7_FACE_ZONE_TABLE_INVALID")
            continue
        name = row.get("name")
        expected_type = 2 if name == INTERIOR_NAME else CANONICAL_BOUNDARIES.get(name)
        if expected_type is None or row.get("zone_type") != expected_type:
            _error(errors, "C7_FACE_ZONE_TYPE_INVALID")
        low, high, count = row.get("min_id"), row.get("max_id"), row.get("face_count")
        if (
            not _valid_int(low)
            or not _valid_int(high)
            or not _valid_int(count)
            or high < low
            or count != high - low + 1
            or count <= 0
        ):
            _error(errors, "C7_FACE_ZONE_COUNT_INVALID")

    adjacency = observation.get("adjacency")
    required_zero = (
        "invalid_interior_faces",
        "invalid_boundary_faces",
        "unknown_cell_references",
        "unassigned_faces",
        "missing_node_references",
    )
    if not isinstance(adjacency, dict):
        _error(errors, "C7_ADJACENCY_INVALID")
    else:
        if any(adjacency.get(key) != 0 for key in required_zero):
            _error(errors, "C7_ADJACENCY_INVALID")
        face_total = sum(
            row.get("face_count", 0) for row in faces if isinstance(row, dict)
        )
        if adjacency.get("total_faces") != face_total:
            _error(errors, "C7_FACE_TOTAL_MISMATCH")
        if adjacency.get("boundary_zone_count") != 10:
            _error(errors, "C7_BOUNDARY_ADJACENCY_INCOMPLETE")
        if adjacency.get("cell_graph_reached_count") != observation.get("cell_count"):
            _error(errors, "C7_CELL_GRAPH_DISCONNECTED")

    bbox = observation.get("used_node_bbox_mm")
    if (
        not isinstance(bbox, dict)
        or not isinstance(bbox.get("min"), list)
        or not isinstance(bbox.get("max"), list)
        or len(bbox.get("min", [])) != 3
        or len(bbox.get("max", [])) != 3
        or not _valid_int(observation.get("used_node_count"))
        or observation.get("used_node_count", 0) <= 0
    ):
        _error(errors, "C7_USED_NODE_BBOX_INVALID")
    else:
        for actual, expected in zip(bbox["min"], EXPECTED_BBOX_MIN_MM):
            if isinstance(actual, bool) or not isinstance(actual, (int, float)) or not math.isfinite(float(actual)) or abs(float(actual) - expected) > BBOX_TOLERANCE_MM:
                _error(errors, "C7_USED_NODE_BBOX_OUT_OF_CONTRACT")
        for actual, expected in zip(bbox["max"], EXPECTED_BBOX_MAX_MM):
            if isinstance(actual, bool) or not isinstance(actual, (int, float)) or not math.isfinite(float(actual)) or abs(float(actual) - expected) > BBOX_TOLERANCE_MM:
                _error(errors, "C7_USED_NODE_BBOX_OUT_OF_CONTRACT")

    return {
        "schema_version": 1,
        "status": PASS_STATUS if not errors else FAIL_STATUS,
        "errors": errors,
        "p1_p6_gates": "NOT_RUN",
        "physics": "NOT_RUN",
        "observation": observation,
    }


def _run_h5dump(h5dump: Path, mesh: Path, *args: str) -> str:
    completed = subprocess.run(
        [str(h5dump), *args, str(mesh)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="strict",
        timeout=120,
        shell=False,
    )
    if completed.returncode != 0:
        raise GateError("C7_H5DUMP_FAILED:{}".format(completed.stderr.strip()))
    return completed.stdout


def _primary_data_block(text: str) -> str:
    marker = text.find("DATA {")
    if marker < 0:
        raise GateError("C7_H5DUMP_DATA_BLOCK_MISSING")
    start = marker + len("DATA {")
    depth = 1
    index = start
    while index < len(text) and depth:
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
        index += 1
    if depth:
        raise GateError("C7_H5DUMP_DATA_BLOCK_UNTERMINATED")
    return text[start : index - 1]


def _numbers(text: str, integer: bool = True) -> List[Any]:
    block = _primary_data_block(text)
    tokens = re.findall(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[Ee][-+]?\d+)?", block)
    return [int(token) for token in tokens] if integer else [float(token) for token in tokens]


def _strings(text: str) -> List[str]:
    block = _primary_data_block(text)
    return [json.loads(token) for token in re.findall(r'"(?:[^"\\]|\\.)*"', block)]


def _dump_numbers(h5dump: Path, mesh: Path, dataset: str, integer: bool = True) -> List[Any]:
    return _numbers(_run_h5dump(h5dump, mesh, "-y", "-w", "0", "-d", dataset), integer)


def _dump_strings(h5dump: Path, mesh: Path, dataset: str) -> List[str]:
    return _strings(_run_h5dump(h5dump, mesh, "-y", "-w", "0", "-d", dataset))


def _names(blob: Sequence[str], count: int) -> List[str]:
    if len(blob) != 1:
        raise GateError("C7_ZONE_NAME_BLOB_INVALID")
    values = blob[0].split(";") if blob[0] else []
    if len(values) != count or any(not value for value in values):
        raise GateError("C7_ZONE_NAME_COUNT_MISMATCH")
    return values


def _dataset_paths(h5dump: Path, mesh: Path) -> List[str]:
    listing = _run_h5dump(h5dump, mesh, "-n")
    return re.findall(r"^\s*dataset\s+(\S+)\s*$", listing, re.MULTILINE)


def _zone_rows(h5dump: Path, mesh: Path, kind: str) -> List[Dict[str, Any]]:
    base = "/meshes/1/{}/zoneTopology".format(kind)
    ids = _dump_numbers(h5dump, mesh, base + "/id")
    lows = _dump_numbers(h5dump, mesh, base + "/minId")
    highs = _dump_numbers(h5dump, mesh, base + "/maxId")
    names = _names(_dump_strings(h5dump, mesh, base + "/name"), len(ids))
    type_field = "cellType" if kind == "cells" else "zoneType"
    types = _dump_numbers(h5dump, mesh, base + "/" + type_field)
    if not (len(ids) == len(lows) == len(highs) == len(names) == len(types)):
        raise GateError("C7_ZONE_TOPOLOGY_LENGTH_MISMATCH")
    rows = []
    for index in range(len(ids)):
        row = {
            "id": ids[index],
            "name": names[index],
            "min_id": lows[index],
            "max_id": highs[index],
            "face_count" if kind == "faces" else "cell_count": highs[index] - lows[index] + 1,
        }
        row[type_field.lower()] = types[index]
        if kind == "faces":
            row["zone_type"] = row.pop("zonetype")
        else:
            row["cell_type"] = row.pop("celltype")
        rows.append(row)
    return rows


class _UnionFind:
    def __init__(self, count: int) -> None:
        self.parent = list(range(count + 1))

    def find(self, value: int) -> int:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: int, right: int) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


def extract_observation(mesh: Path, h5dump: Path) -> Dict[str, Any]:
    """Extract only the topology required by the semantic gate."""
    paths = set(_dataset_paths(h5dump, mesh))
    version = _dump_strings(h5dump, mesh, "/settings/Version")
    solver = _dump_strings(h5dump, mesh, "/settings/Solver")
    cell_rows = _zone_rows(h5dump, mesh, "cells")
    face_rows = _zone_rows(h5dump, mesh, "faces")
    if len(version) != 1 or len(solver) != 1 or len(cell_rows) != 1:
        raise GateError("C7_HDF5_HEADER_INVALID")
    cell_count = cell_rows[0]["cell_count"]
    union = _UnionFind(cell_count)
    used_nodes = set()
    invalid_interior = invalid_boundary = unknown_cells = unassigned = 0

    for index, row in enumerate(face_rows, 1):
        required = (
            "/meshes/1/faces/c0/{0}",
            "/meshes/1/faces/c1/{0}",
            "/meshes/1/faces/nodes/{0}/nnodes",
            "/meshes/1/faces/nodes/{0}/nodes",
        )
        datasets = [value.format(index) for value in required]
        if any(dataset not in paths for dataset in datasets):
            raise GateError("C7_FACE_SEGMENT_DATASET_MISSING")
        c0 = _dump_numbers(h5dump, mesh, datasets[0])
        c1 = _dump_numbers(h5dump, mesh, datasets[1])
        nnodes = _dump_numbers(h5dump, mesh, datasets[2])
        nodes = _dump_numbers(h5dump, mesh, datasets[3])
        if len(c0) != row["face_count"] or len(c1) != row["face_count"] or len(nnodes) != row["face_count"] or sum(nnodes) != len(nodes):
            unassigned += abs(row["face_count"] - min(len(c0), len(c1), len(nnodes))) + 1
            continue
        used_nodes.update(nodes)
        interior = row["zone_type"] == 2
        for left, right in zip(c0, c1):
            left_ok = 1 <= left <= cell_count
            right_ok = 1 <= right <= cell_count
            if (left and not left_ok) or (right and not right_ok):
                unknown_cells += 1
            if interior:
                if not left_ok or not right_ok or left == right:
                    invalid_interior += 1
                else:
                    union.union(left, right)
            elif not left_ok or right != 0:
                invalid_boundary += 1

    referenced_coordinates: Dict[int, Tuple[float, float, float]] = {}
    node_ids = _dump_numbers(h5dump, mesh, "/meshes/1/nodes/zoneTopology/id")
    node_lows = _dump_numbers(h5dump, mesh, "/meshes/1/nodes/zoneTopology/minId")
    node_highs = _dump_numbers(h5dump, mesh, "/meshes/1/nodes/zoneTopology/maxId")
    if not (len(node_ids) == len(node_lows) == len(node_highs)):
        raise GateError("C7_NODE_TOPOLOGY_LENGTH_MISMATCH")
    for index, (low, high) in enumerate(zip(node_lows, node_highs), 1):
        dataset = "/meshes/1/nodes/coords/{}".format(index)
        if dataset not in paths:
            raise GateError("C7_NODE_COORD_DATASET_MISSING")
        values = _dump_numbers(h5dump, mesh, dataset, integer=False)
        if len(values) != (high - low + 1) * 3:
            raise GateError("C7_NODE_COORD_LENGTH_MISMATCH")
        for offset in range(high - low + 1):
            node_id = low + offset
            if node_id in used_nodes:
                start = offset * 3
                referenced_coordinates[node_id] = tuple(values[start : start + 3])  # type: ignore[assignment]
    missing_nodes = len(used_nodes - set(referenced_coordinates))
    coords = list(referenced_coordinates.values())
    bbox = {
        "min": [min(value[axis] for value in coords) for axis in range(3)] if coords else [],
        "max": [max(value[axis] for value in coords) for axis in range(3)] if coords else [],
    }
    first_root = union.find(1) if cell_count else -1
    reached = sum(1 for value in range(1, cell_count + 1) if union.find(value) == first_root)
    return {
        "mesh_sha256": hashlib.sha256(mesh.read_bytes()).hexdigest(),
        "format_version": version[0],
        "solver": solver[0],
        "cell_zones": cell_rows,
        "face_zones": face_rows,
        "cell_count": cell_count,
        "used_node_count": len(used_nodes),
        "used_node_bbox_mm": bbox,
        "adjacency": {
            "total_faces": sum(row["face_count"] for row in face_rows),
            "boundary_zone_count": sum(1 for row in face_rows if row["zone_type"] != 2),
            "invalid_interior_faces": invalid_interior,
            "invalid_boundary_faces": invalid_boundary,
            "unknown_cell_references": unknown_cells,
            "unassigned_faces": unassigned,
            "missing_node_references": missing_nodes,
            "cell_graph_reached_count": reached,
        },
    }


def _discover_h5dump(explicit: Optional[str]) -> Path:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    if os.environ.get("AIRJET_H5DUMP"):
        candidates.append(Path(os.environ["AIRJET_H5DUMP"]))
    candidates.extend(
        Path(root) / "ANSYS Inc" / "ANSYS Student" / "v261" / "tp" / "hdf5" / "winx64" / "h5dump.exe"
        for root in ("D:/ansys", "C:/Program Files")
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise GateError("C7_H5DUMP_NOT_FOUND")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mesh", type=Path)
    parser.add_argument("--h5dump")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        mesh = args.mesh.resolve(strict=True)
        observation = extract_observation(mesh, _discover_h5dump(args.h5dump))
        result = validate_observation(observation)
    except (GateError, OSError, ValueError, subprocess.SubprocessError) as exc:
        result = {
            "schema_version": 1,
            "status": FAIL_STATUS,
            "errors": [str(exc)],
            "p1_p6_gates": "NOT_RUN",
            "physics": "NOT_RUN",
        }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        with args.output.open("w", encoding="ascii", newline="\n") as handle:
            handle.write(rendered)
    sys.stdout.write(rendered)
    return 0 if result["status"] == PASS_STATUS else 2


if __name__ == "__main__":
    raise SystemExit(main())
