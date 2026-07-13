#!/usr/bin/env python3
"""Recompute AirJet Mini chart values from versioned full-page pixel coordinates."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def scale_x(row: dict[str, str]) -> float:
    x = float(row["x_px"])
    x0 = float(row["x0_px"])
    x1 = float(row["x1_px"])
    lo = float(row["x_axis_min"])
    hi = float(row["x_axis_max"])
    return lo + (x - x0) / (x1 - x0) * (hi - lo)


def scale_y(row: dict[str, str]) -> float:
    y = float(row["y_px"])
    y0 = float(row["y0_px"])
    y1 = float(row["y1_px"])
    lo = float(row["y_axis_min"])
    hi = float(row["y_axis_max"])
    return lo + (y0 - y) / (y0 - y1) * (hi - lo)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    evidence = args.repo.resolve() / "airjet-simulation" / "evidence"
    pixels = read_csv(evidence / "airjet_mini_curve_pixels.csv")
    targets = read_csv(evidence / "airjet_mini_performance_curve_digitized.csv")
    target_by_power = {float(row["power_W"]): row for row in targets}
    failures: list[str] = []

    grouped: dict[float, dict[str, float]] = {}
    for row in pixels:
        nominal = float(row["power_nominal_W"])
        x_value = scale_x(row)
        y_value = scale_y(row)
        grouped.setdefault(nominal, {})[row["series"]] = y_value
        if abs(x_value - nominal) > 0.003:
            failures.append(
                f"x calibration mismatch at nominal {nominal:.2f} W: {x_value:.4f} W"
            )

    print("power_W,net_heat_from_pixels_W,system_noise_from_pixels_dBA")
    for power in sorted(grouped):
        values = grouped[power]
        print(f"{power:.2f},{values['net_heat']:.3f},{values['system_noise']:.3f}")
        if args.check:
            target = target_by_power.get(power)
            if target is None:
                failures.append(f"canonical curve lacks {power:.2f} W row")
                continue
            heat_error = abs(values["net_heat"] - float(target["net_heat_dissipation_W"]))
            noise_error = abs(
                values["system_noise"] - float(target["system_noise_at_50cm_dBA"])
            )
            if heat_error > float(target["heat_uncertainty_W"]):
                failures.append(f"heat value outside uncertainty at {power:.2f} W")
            if noise_error > float(target["noise_uncertainty_dBA"]):
                failures.append(f"noise value outside uncertainty at {power:.2f} W")

    if failures:
        print("FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    if args.check:
        print("CURVE_DIGITIZATION_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
