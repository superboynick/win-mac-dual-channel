#!/usr/bin/env python3
"""Populate the AirJet Mini evidence/layout experiment notebook."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
NOTEBOOK = HERE / "airjet-mini-layout-baseline.ipynb"


def markdown(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.splitlines(keepends=True),
    }


data = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
data["cells"] = [
    markdown(
        """# AirJet Mini full-product evidence and layout baseline

Objective: turn the current product evidence and patent-bounded dimensions into auditable full-product layout candidates. This notebook does **not** claim a true internal cell count.

Success criteria:

- load the versioned evidence tables directly from the repository;
- verify the 1 W heat-accounting identity;
- preserve the Mini performance chart's right axis as 50 cm system noise, not airflow;
- enumerate Layout-L/M/S geometric candidates without exceeding 27.5 x 41.5 mm;
- label image margins, cell shape, and wall allowance as assumptions for later calibration.
"""
    ),
    code(
        """# Setup: standard-library-only for cross-machine reproducibility
from __future__ import annotations

import csv
from pathlib import Path
from pprint import pprint


def find_repo(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "airjet-simulation" / "parameters").is_dir():
            return candidate
    raise FileNotFoundError("Run inside the win-mac-dual-channel repository")


REPO = find_repo(Path.cwd().resolve())
PROJECT = REPO / "airjet-simulation"
REPO
"""
    ),
    markdown(
        """## Evidence load and invariants

The data sheet directly supports product envelope, maximum power, net/total heat, 1750 Pa back pressure, 21 dBA system noise at 50 cm, and 11 g mass. Patent ranges constrain internal candidates but are not exact Mini production dimensions.
"""
    ),
    code(
        """def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


registry = read_csv(PROJECT / "parameters" / "full_product_parameter_registry.csv")
curve = read_csv(PROJECT / "evidence" / "airjet_mini_performance_curve_digitized.csv")

registry_by_id = {row["id"]: row for row in registry}
required_ids = {"D001", "D002", "D003", "D004", "D005", "D006", "D011", "D012", "D013"}
missing = required_ids - registry_by_id.keys()
assert not missing, f"Missing direct product parameters: {sorted(missing)}"

assert "system_noise_at_50cm_dBA" in curve[0], "The chart right axis must be system noise"
assert "delivered_airflow_chart_units" not in curve[0], "Obsolete airflow interpretation detected"

targets = {
    "width_mm": float(registry_by_id["D001"]["initial_value"]),
    "length_mm": float(registry_by_id["D002"]["initial_value"]),
    "thickness_mm": float(registry_by_id["D003"]["initial_value"]),
    "power_W": float(registry_by_id["D004"]["initial_value"]),
    "total_heat_W": float(registry_by_id["D005"]["initial_value"]),
    "net_heat_W": float(registry_by_id["D006"]["initial_value"]),
    "back_pressure_Pa": float(registry_by_id["D011"]["initial_value"]),
    "noise_dBA": float(registry_by_id["D012"]["initial_value"]),
    "mass_g": float(registry_by_id["D013"]["initial_value"]),
}

assert abs(targets["net_heat_W"] + targets["power_W"] - targets["total_heat_W"]) < 1e-12
pprint(targets)
"""
    ),
    code(
        """# Digitized official curve points; noise values are approximate except the 1 W endpoint
curve_numeric = [
    {
        "power_W": float(row["power_W"]),
        "net_heat_W": float(row["net_heat_dissipation_W"]),
        "noise_dBA": float(row["system_noise_at_50cm_dBA"]),
        "status": row["status"],
    }
    for row in curve
]
curve_numeric
"""
    ),
    markdown(
        """## Layout candidate enumeration

This is a geometry filter, not a reconstruction result. The membrane is temporarily treated as square in plan view; side margins, inlet/exhaust allowance, and cell wall allowance are calibration assumptions. Candidates that fit proceed to image, modal, power, airflow/back-pressure, and thermal gates.
"""
    ),
    code(
        """# Explicit assumptions: change here and rerun, but do not promote them to product facts
assumptions = {
    "side_margin_mm": 1.0,
    "inlet_exhaust_allowance_mm": 5.0,
    "cell_wall_mm": 0.25,
}

families = {
    "Layout-L": {"membrane_mm": [8.0, 9.0, 10.0], "nx": [2, 3], "ny": [3, 4]},
    "Layout-M": {"membrane_mm": [6.0, 7.0, 8.0], "nx": [3], "ny": [4, 5]},
    "Layout-S": {"membrane_mm": [4.5, 5.0, 5.5, 6.0], "nx": [3, 4], "ny": [5, 6]},
}


def used_span(count: int, membrane: float, wall: float) -> float:
    return count * membrane + (count - 1) * wall


candidates = []
for family, spec in families.items():
    for membrane in spec["membrane_mm"]:
        for nx in spec["nx"]:
            for ny in spec["ny"]:
                used_width = used_span(nx, membrane, assumptions["cell_wall_mm"]) + 2 * assumptions["side_margin_mm"]
                used_length = used_span(ny, membrane, assumptions["cell_wall_mm"]) + assumptions["inlet_exhaust_allowance_mm"]
                fits = used_width <= targets["width_mm"] and used_length <= targets["length_mm"]
                candidates.append({
                    "family": family,
                    "membrane_mm": membrane,
                    "nx": nx,
                    "ny": ny,
                    "cell_count": nx * ny,
                    "used_width_mm": round(used_width, 3),
                    "used_length_mm": round(used_length, 3),
                    "width_margin_mm": round(targets["width_mm"] - used_width, 3),
                    "length_margin_mm": round(targets["length_mm"] - used_length, 3),
                    "geometry_fit": fits,
                })

feasible = [row for row in candidates if row["geometry_fit"]]
len(candidates), len(feasible)
"""
    ),
    code(
        """# Compact, deterministic output sorted by family, cell count, and membrane size
feasible_sorted = sorted(
    feasible,
    key=lambda row: (row["family"], row["cell_count"], row["membrane_mm"]),
)
for row in feasible_sorted:
    print(
        f"{row['family']:8s}  {row['nx']}x{row['ny']}={row['cell_count']:2d} cells  "
        f"mem={row['membrane_mm']:4.1f} mm  "
        f"used={row['used_width_mm']:5.2f}x{row['used_length_mm']:5.2f} mm  "
        f"remaining={row['width_margin_mm']:5.2f}x{row['length_margin_mm']:5.2f} mm"
    )
"""
    ),
    markdown(
        """## Interpretation and next gate

- A geometry fit only proves that a hypothetical square-cell array fits inside the package envelope.
- Patent values of 6-8 mm are stronger candidates than values outside that range, but still are not exact product dimensions.
- Candidate ranking must next include official-image proportions, modal frequency/displacement, `N_cell x P_cell + P_driver <= 1 W`, a separate pressure-capability scan up to the reported 1750 Pa, and the 4.25 W net/5.25 W total heat targets. The public sheet does not give the flow corresponding to 1750 Pa.
- Public Mini material currently has no direct numeric airflow curve; do not invent one from the noise axis.

Decision: keep Layout-L/M/S alive until the P0 image constraints and P2/P3 physics eliminate candidates.
"""
    ),
]

NOTEBOOK.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {NOTEBOOK}")
