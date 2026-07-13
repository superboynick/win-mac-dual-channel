#!/usr/bin/env python3
"""Cross-check AirJet Mini Gen1 drawn vent positions in two official renders.

This script records raw pixels, performs two independent homographies, and
propagates manual pixel uncertainty by deterministic Monte Carlo.  Results are
image-inference evidence only; the four drawn slots are not proven production
inlet groups and do not reveal the internal cell count.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from extract_official_image_geometry import perspective_coefficients


PIXELS_PER_MM = 20
RECTIFIED_SIZE = (550, 830)  # 27.5 x 41.5 mm
CORNER_UNCERTAINTY_PX = 3.0
ENDPOINT_UNCERTAINTY_PX = 2.0
MONTE_CARLO_SAMPLES = 10_000
MONTE_CARLO_SEED = 20260713

VIEWS = {
    "flow_636": {
        "size": (636, 387),
        "rgb_sha256": "13d513ff90069afa96ec034ca0d4ae03e5c18205014e4508bc9b7bd702dfbe0d",
        "mask_sha256": "f711b34baa31b0050ea642b0d7167af1e6aa29b4be4fab3a1da57570e79341fb",
        # Output order: rear-left, rear-right, outlet-right, outlet-left.
        "quad": ((318.0, 53.0), (538.0, 172.0), (241.0, 337.0), (22.0, 221.0)),
        "features": {
            "V01": ((262.7, 156.3), (357.8, 104.6)),
            "V02": ((340.5, 200.7), (436.0, 146.4)),
            "V03": ((144.4, 221.7), (246.2, 166.3)),
            "V04": ((221.9, 269.5), (324.1, 211.2)),
        },
    },
    "upper_547": {
        "size": (547, 257),
        "rgb_sha256": "c5286aadcf3a42d338b70cfeaed8fa27f0a6f171cb7621981e34f96378ff4956",
        "mask_sha256": "fb7c08ad552f432f5d70c52e3f34749da17a8a7eb8b4d2b04322b57cd011dcb2",
        # The extracted JPEG is vertically flipped in PDF placement.  This
        # order keeps the flex/rear edge at Y=0 and outlet edge at Y=41.5 mm.
        "quad": ((463.0, 130.0), (274.0, 221.0), (21.0, 110.0), (207.0, 8.0)),
        "features": {
            "V01": ((292.4, 122.8), (374.8, 158.8)),
            "V02": ((225.3, 152.2), (308.1, 186.8)),
            "V03": ((190.4, 77.1), (279.0, 116.0)),
            "V04": ((124.0, 109.0), (212.1, 145.8)),
        },
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    location = (len(ordered) - 1) * probability
    lower = math.floor(location)
    upper = math.ceil(location)
    if lower == upper:
        return ordered[lower]
    fraction = location - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def coefficients_source_to_rectified(quad: tuple[tuple[float, float], ...]) -> tuple[float, ...]:
    width, height = RECTIFIED_SIZE
    destination = ((0.0, 0.0), (width - 1.0, 0.0), (width - 1.0, height - 1.0), (0.0, height - 1.0))
    return perspective_coefficients(quad, destination)


def map_point(coefficients: tuple[float, ...], point: tuple[float, float]) -> tuple[float, float]:
    x, y = point
    denominator = coefficients[6] * x + coefficients[7] * y + 1.0
    return (
        (coefficients[0] * x + coefficients[1] * y + coefficients[2]) / denominator,
        (coefficients[3] * x + coefficients[4] * y + coefficients[5]) / denominator,
    )


def load_composited(rgb_path: Path, mask_path: Path, view: dict[str, object]) -> Image.Image:
    if sha256(rgb_path) != view["rgb_sha256"]:
        raise SystemExit(f"RGB hash mismatch: {rgb_path}")
    if sha256(mask_path) != view["mask_sha256"]:
        raise SystemExit(f"Mask hash mismatch: {mask_path}")
    rgb = Image.open(rgb_path).convert("RGB")
    mask = Image.open(mask_path).convert("L")
    if rgb.size != view["size"] or mask.size != view["size"]:
        raise ValueError(f"Unexpected dimensions for {rgb_path}")
    return Image.composite(rgb, Image.new("RGB", rgb.size, "white"), mask)


def annotate_source(image: Image.Image, view_name: str, view: dict[str, object]) -> Image.Image:
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=14)
    quad = [tuple(round(value) for value in point) for point in view["quad"]]
    draw.line(quad + [quad[0]], fill=(220, 0, 0), width=3)
    for index, (x, y) in enumerate(quad):
        draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(255, 180, 0), outline="black")
        draw.text((x + 5, y - 15), f"Q{index} ({x},{y})", fill=(160, 0, 0), font=font)
    for feature_id, (point_a, point_b) in view["features"].items():
        draw.line((point_a, point_b), fill=(0, 150, 255), width=3)
        for point in (point_a, point_b):
            x, y = point
            draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(0, 220, 255), outline="black")
        midpoint = ((point_a[0] + point_b[0]) / 2, (point_a[1] + point_b[1]) / 2)
        draw.text(midpoint, feature_id, fill=(0, 80, 180), font=font)
    draw.rectangle((4, canvas.height - 34, canvas.width - 4, canvas.height - 4), fill="white")
    draw.text((8, canvas.height - 28), f"{view_name}: quad +/-3 px; PCA endpoints +/-2 px; inference only", fill=(150, 0, 0), font=font)
    return canvas


def rectify_and_annotate(image: Image.Image, view_name: str, view: dict[str, object]) -> Image.Image:
    width, height = RECTIFIED_SIZE
    destination = ((0.0, 0.0), (width - 1.0, 0.0), (width - 1.0, height - 1.0), (0.0, height - 1.0))
    output_to_input = perspective_coefficients(destination, view["quad"])
    rectified = image.transform(
        RECTIFIED_SIZE,
        Image.Transform.PERSPECTIVE,
        output_to_input,
        resample=Image.Resampling.BICUBIC,
        fillcolor="white",
    )
    draw = ImageDraw.Draw(rectified)
    font = ImageFont.load_default(size=14)
    for mm in range(0, 28, 5):
        x = mm * PIXELS_PER_MM
        draw.line((x, 0, x, height - 1), fill=(220, 50, 50), width=1)
    for mm in range(0, 42, 5):
        y = mm * PIXELS_PER_MM
        draw.line((0, y, width - 1, y), fill=(50, 90, 220), width=1)
    source_to_output = coefficients_source_to_rectified(view["quad"])
    for feature_id, (point_a, point_b) in view["features"].items():
        mapped_a = map_point(source_to_output, point_a)
        mapped_b = map_point(source_to_output, point_b)
        draw.line((mapped_a, mapped_b), fill=(255, 170, 0), width=4)
        midpoint = ((mapped_a[0] + mapped_b[0]) / 2, (mapped_a[1] + mapped_b[1]) / 2)
        draw.text(midpoint, feature_id, fill=(255, 220, 0), font=font)
    draw.rectangle((5, height - 40, width - 5, height - 5), fill="white", outline=(170, 0, 0))
    draw.text((10, height - 34), f"{view_name}: independent homography; four drawn vents are not cell-count evidence", fill=(150, 0, 0), font=font)
    return rectified


def monte_carlo(
    view: dict[str, object],
    random_source: random.Random,
) -> dict[str, dict[str, tuple[float, float, float]]]:
    samples = {
        feature_id: {"center_x_mm": [], "center_y_mm": [], "length_mm": []}
        for feature_id in view["features"]
    }
    for _ in range(MONTE_CARLO_SAMPLES):
        perturbed_quad = tuple(
            (
                x + random_source.uniform(-CORNER_UNCERTAINTY_PX, CORNER_UNCERTAINTY_PX),
                y + random_source.uniform(-CORNER_UNCERTAINTY_PX, CORNER_UNCERTAINTY_PX),
            )
            for x, y in view["quad"]
        )
        coefficients = coefficients_source_to_rectified(perturbed_quad)
        for feature_id, (point_a, point_b) in view["features"].items():
            perturbed = []
            for x, y in (point_a, point_b):
                perturbed.append(
                    (
                        x + random_source.uniform(-ENDPOINT_UNCERTAINTY_PX, ENDPOINT_UNCERTAINTY_PX),
                        y + random_source.uniform(-ENDPOINT_UNCERTAINTY_PX, ENDPOINT_UNCERTAINTY_PX),
                    )
                )
            mapped_a, mapped_b = (map_point(coefficients, point) for point in perturbed)
            ax, ay = (value / PIXELS_PER_MM for value in mapped_a)
            bx, by = (value / PIXELS_PER_MM for value in mapped_b)
            samples[feature_id]["center_x_mm"].append((ax + bx) / 2)
            samples[feature_id]["center_y_mm"].append((ay + by) / 2)
            samples[feature_id]["length_mm"].append(math.hypot(ax - bx, ay - by))

    summary: dict[str, dict[str, tuple[float, float, float]]] = {}
    for feature_id, metrics in samples.items():
        summary[feature_id] = {
            name: (quantile(values, 0.5), quantile(values, 0.025), quantile(values, 0.975))
            for name, values in metrics.items()
        }
    return summary


def nominal_metrics(view: dict[str, object]) -> dict[str, dict[str, object]]:
    coefficients = coefficients_source_to_rectified(view["quad"])
    result = {}
    for feature_id, (point_a, point_b) in view["features"].items():
        mapped_a_px = map_point(coefficients, point_a)
        mapped_b_px = map_point(coefficients, point_b)
        mapped_a = tuple(value / PIXELS_PER_MM for value in mapped_a_px)
        mapped_b = tuple(value / PIXELS_PER_MM for value in mapped_b_px)
        result[feature_id] = {
            "point_a": point_a,
            "point_b": point_b,
            "mapped_a": mapped_a,
            "mapped_b": mapped_b,
            "center_x_mm": (mapped_a[0] + mapped_b[0]) / 2,
            "center_y_mm": (mapped_a[1] + mapped_b[1]) / 2,
            "length_mm": math.hypot(mapped_a[0] - mapped_b[0], mapped_a[1] - mapped_b[1]),
        }
    return result


def write_results(
    output_dir: Path,
    nominal: dict[str, dict[str, dict[str, object]]],
    uncertainty: dict[str, dict[str, dict[str, tuple[float, float, float]]]],
) -> None:
    fieldnames = [
        "view_id", "feature_id", "source_a_x_px", "source_a_y_px", "source_b_x_px", "source_b_y_px",
        "rectified_a_x_mm", "rectified_a_y_mm", "rectified_b_x_mm", "rectified_b_y_mm",
        "center_x_mm", "center_y_mm", "length_mm",
        "mc_center_x_median_mm", "mc_center_x_ci95_low_mm", "mc_center_x_ci95_high_mm",
        "mc_center_y_median_mm", "mc_center_y_ci95_low_mm", "mc_center_y_ci95_high_mm",
        "mc_length_median_mm", "mc_length_ci95_low_mm", "mc_length_ci95_high_mm",
        "evidence_class", "allowed_use", "forbidden_use",
    ]
    rows = []
    for view_name in VIEWS:
        for feature_id in sorted(nominal[view_name]):
            item = nominal[view_name][feature_id]
            mc = uncertainty[view_name][feature_id]
            rows.append(
                {
                    "view_id": view_name,
                    "feature_id": feature_id,
                    "source_a_x_px": f"{item['point_a'][0]:.1f}",
                    "source_a_y_px": f"{item['point_a'][1]:.1f}",
                    "source_b_x_px": f"{item['point_b'][0]:.1f}",
                    "source_b_y_px": f"{item['point_b'][1]:.1f}",
                    "rectified_a_x_mm": f"{item['mapped_a'][0]:.3f}",
                    "rectified_a_y_mm": f"{item['mapped_a'][1]:.3f}",
                    "rectified_b_x_mm": f"{item['mapped_b'][0]:.3f}",
                    "rectified_b_y_mm": f"{item['mapped_b'][1]:.3f}",
                    "center_x_mm": f"{item['center_x_mm']:.3f}",
                    "center_y_mm": f"{item['center_y_mm']:.3f}",
                    "length_mm": f"{item['length_mm']:.3f}",
                    "mc_center_x_median_mm": f"{mc['center_x_mm'][0]:.3f}",
                    "mc_center_x_ci95_low_mm": f"{mc['center_x_mm'][1]:.3f}",
                    "mc_center_x_ci95_high_mm": f"{mc['center_x_mm'][2]:.3f}",
                    "mc_center_y_median_mm": f"{mc['center_y_mm'][0]:.3f}",
                    "mc_center_y_ci95_low_mm": f"{mc['center_y_mm'][1]:.3f}",
                    "mc_center_y_ci95_high_mm": f"{mc['center_y_mm'][2]:.3f}",
                    "mc_length_median_mm": f"{mc['length_mm'][0]:.3f}",
                    "mc_length_ci95_low_mm": f"{mc['length_mm'][1]:.3f}",
                    "mc_length_ci95_high_mm": f"{mc['length_mm'][2]:.3f}",
                    "evidence_class": "I",
                    "allowed_use": "candidate top-cover vent placement and cross-view systematic-error estimate",
                    "forbidden_use": "production inlet count, cell count, manufacturing tolerance, internal membrane geometry",
                }
            )
    with (output_dir / "gen1_vent_homography_results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    comparison_fields = [
        "feature_id", "flow_center_x_mm", "upper_center_x_mm", "abs_center_x_difference_mm",
        "flow_center_y_mm", "upper_center_y_mm", "abs_center_y_difference_mm",
        "flow_length_mm", "upper_length_mm", "abs_length_difference_mm", "interpretation",
    ]
    comparisons = []
    for feature_id in sorted(VIEWS["flow_636"]["features"]):
        flow = nominal["flow_636"][feature_id]
        upper = nominal["upper_547"][feature_id]
        comparisons.append(
            {
                "feature_id": feature_id,
                "flow_center_x_mm": f"{flow['center_x_mm']:.3f}",
                "upper_center_x_mm": f"{upper['center_x_mm']:.3f}",
                "abs_center_x_difference_mm": f"{abs(flow['center_x_mm'] - upper['center_x_mm']):.3f}",
                "flow_center_y_mm": f"{flow['center_y_mm']:.3f}",
                "upper_center_y_mm": f"{upper['center_y_mm']:.3f}",
                "abs_center_y_difference_mm": f"{abs(flow['center_y_mm'] - upper['center_y_mm']):.3f}",
                "flow_length_mm": f"{flow['length_mm']:.3f}",
                "upper_length_mm": f"{upper['length_mm']:.3f}",
                "abs_length_difference_mm": f"{abs(flow['length_mm'] - upper['length_mm']):.3f}",
                "interpretation": "cross-view difference is model-form uncertainty and dominates simple endpoint-pixel precision",
            }
        )
    with (output_dir / "gen1_vent_cross_view_comparison.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=comparison_fields)
        writer.writeheader()
        writer.writerows(comparisons)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flow-rgb", type=Path, required=True)
    parser.add_argument("--flow-mask", type=Path, required=True)
    parser.add_argument("--upper-rgb", type=Path, required=True)
    parser.add_argument("--upper-mask", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    paths = {
        "flow_636": (args.flow_rgb, args.flow_mask),
        "upper_547": (args.upper_rgb, args.upper_mask),
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    nominal = {}
    uncertainty = {}
    random_source = random.Random(MONTE_CARLO_SEED)
    for view_name, view in VIEWS.items():
        image = load_composited(*paths[view_name], view)
        annotate_source(image, view_name, view).save(args.out_dir / f"gen1_{view_name}_source_annotated.png")
        rectify_and_annotate(image, view_name, view).save(args.out_dir / f"gen1_{view_name}_rectified.png")
        nominal[view_name] = nominal_metrics(view)
        uncertainty[view_name] = monte_carlo(view, random_source)
    write_results(args.out_dir, nominal, uncertainty)
    print(
        f"PASS views={len(VIEWS)} features={sum(len(view['features']) for view in VIEWS.values())} "
        f"samples_per_view={MONTE_CARLO_SAMPLES} out_dir={args.out_dir}"
    )


if __name__ == "__main__":
    main()
