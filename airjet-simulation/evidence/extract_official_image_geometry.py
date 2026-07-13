#!/usr/bin/env python3
"""Create auditable AirJet Mini Gen1 image-geometry aids.

The input is the 636 x 387 RGB object and its 636 x 387 soft mask extracted
from the official one-page AirJet Mini data sheet with Poppler ``pdfimages``.
The script does not claim that the marketing render is a manufacturing
drawing.  It only records the manually selected top-plane quadrilateral and
creates a projective rectification for normalized intake-layout comparison.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


EXPECTED_RGB_SHA256 = "13d513ff90069afa96ec034ca0d4ae03e5c18205014e4508bc9b7bd702dfbe0d"
EXPECTED_MASK_SHA256 = "f711b34baa31b0050ea642b0d7167af1e6aa29b4be4fab3a1da57570e79341fb"
EXPECTED_SIZE = (636, 387)
EXPECTED_PAGE_RENDER_SHA256 = "9686da3780d01f757daff44c145c1f110ac9121580a33b97f8ff42ac9be949fa"
EXPECTED_PAGE_RENDER_SIZE = (2550, 6450)
SOURCE_PDF_SHA256 = "822fbb7e9735a5505734a291083fed7901c1fdfa01cb7de369679e4d41fd19bd"

# Clockwise: rear-left, rear-right, outlet-side right, outlet-side left.
# Selection uncertainty is +/- 3 px per coordinate on the extracted object.
SOURCE_TOP_QUAD = ((318.0, 53.0), (538.0, 172.0), (241.0, 337.0), (22.0, 221.0))
CORNER_UNCERTAINTY_PX = 3.0

PRODUCT_WIDTH_MM = 27.5
PRODUCT_LENGTH_MM = 41.5
PIXELS_PER_MM = 20
RECTIFIED_SIZE = (
    round(PRODUCT_WIDTH_MM * PIXELS_PER_MM),
    round(PRODUCT_LENGTH_MM * PIXELS_PER_MM),
)

# Read manually from the rectified 20 px/mm image.  These are top-cover vent
# envelopes in a marketing render, not internal cell boundaries.
VENT_BOUNDS_MM = {
    "V01_rear_left": (7.25, 3.00, 8.95, 17.10),
    "V02_rear_right": (17.25, 3.00, 18.95, 17.30),
    "V03_outlet_left": (7.15, 19.00, 8.95, 33.50),
    "V04_outlet_right": (17.50, 19.20, 19.10, 34.10),
}
VENT_READOUT_UNCERTAINTY_MM = 0.50
CROSS_SECTION_CROP = (75, 2300, 2475, 3400)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def solve_linear(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Solve a small dense system using Gaussian elimination with pivoting."""

    n = len(vector)
    augmented = [row[:] + [value] for row, value in zip(matrix, vector)]
    for column in range(n):
        pivot = max(range(column, n), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("Singular homography system")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        pivot_value = augmented[column][column]
        augmented[column] = [value / pivot_value for value in augmented[column]]
        for row in range(n):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                value - factor * pivot_entry
                for value, pivot_entry in zip(augmented[row], augmented[column])
            ]
    return [augmented[row][-1] for row in range(n)]


def perspective_coefficients(
    output_points: tuple[tuple[float, float], ...],
    input_points: tuple[tuple[float, float], ...],
) -> tuple[float, ...]:
    """Return Pillow coefficients mapping output coordinates to input pixels."""

    matrix: list[list[float]] = []
    vector: list[float] = []
    for (u, v), (x, y) in zip(output_points, input_points):
        matrix.append([u, v, 1.0, 0.0, 0.0, 0.0, -u * x, -v * x])
        vector.append(x)
        matrix.append([0.0, 0.0, 0.0, u, v, 1.0, -u * y, -v * y])
        vector.append(y)
    return tuple(solve_linear(matrix, vector))


def load_composited(rgb_path: Path, mask_path: Path) -> Image.Image:
    rgb = Image.open(rgb_path).convert("RGB")
    mask = Image.open(mask_path).convert("L")
    if rgb.size != EXPECTED_SIZE or mask.size != EXPECTED_SIZE:
        raise ValueError(f"Expected {EXPECTED_SIZE}, got RGB={rgb.size}, mask={mask.size}")
    return Image.composite(rgb, Image.new("RGB", rgb.size, "white"), mask)


def label_font(size: int = 14) -> ImageFont.ImageFont:
    return ImageFont.load_default(size=size)


def annotate_source(image: Image.Image) -> Image.Image:
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)
    font = label_font()
    for x in range(0, canvas.width, 50):
        draw.line((x, 0, x, canvas.height), fill=(210, 210, 210), width=1)
        draw.text((x + 2, 2), str(x), fill=(90, 90, 90), font=font)
    for y in range(0, canvas.height, 50):
        draw.line((0, y, canvas.width, y), fill=(210, 210, 210), width=1)
        draw.text((2, y + 2), str(y), fill=(90, 90, 90), font=font)

    points = [tuple(round(value) for value in point) for point in SOURCE_TOP_QUAD]
    draw.line(points + [points[0]], fill=(220, 40, 40), width=3)
    names = ("Q0 rear-left", "Q1 rear-right", "Q2 outlet-right", "Q3 outlet-left")
    for name, (x, y) in zip(names, points):
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(255, 180, 0), outline=(0, 0, 0))
        draw.text((x + 7, y - 18), f"{name} ({x},{y})", fill=(180, 0, 0), font=font)
    draw.rectangle((6, canvas.height - 40, canvas.width - 6, canvas.height - 6), fill="white")
    draw.text(
        (12, canvas.height - 34),
        "Manual top-plane quad; +/-3 px selection. Marketing render, not a manufacturing drawing.",
        fill=(150, 0, 0),
        font=font,
    )
    return canvas


def rectify(image: Image.Image) -> Image.Image:
    width, height = RECTIFIED_SIZE
    output_points = ((0.0, 0.0), (width - 1.0, 0.0), (width - 1.0, height - 1.0), (0.0, height - 1.0))
    coefficients = perspective_coefficients(output_points, SOURCE_TOP_QUAD)
    rectified = image.transform(
        RECTIFIED_SIZE,
        Image.Transform.PERSPECTIVE,
        coefficients,
        resample=Image.Resampling.BICUBIC,
        fillcolor="white",
    )
    draw = ImageDraw.Draw(rectified)
    font = label_font()
    for mm in range(0, 28, 5):
        x = mm * PIXELS_PER_MM
        draw.line((x, 0, x, height - 1), fill=(220, 50, 50), width=1)
        draw.text((x + 3, 3), f"X={mm} mm", fill=(160, 0, 0), font=font)
    for mm in range(0, 42, 5):
        y = mm * PIXELS_PER_MM
        draw.line((0, y, width - 1, y), fill=(50, 90, 220), width=1)
        draw.text((3, y + 3), f"Y={mm} mm", fill=(0, 40, 160), font=font)
    for name, (x0_mm, y0_mm, x1_mm, y1_mm) in VENT_BOUNDS_MM.items():
        box = tuple(
            round(value * PIXELS_PER_MM)
            for value in (x0_mm, y0_mm, x1_mm, y1_mm)
        )
        draw.rectangle(box, outline=(255, 170, 0), width=3)
        draw.text((box[0] + 3, box[1] + 3), name.split("_")[0], fill=(255, 210, 0), font=font)
    draw.rectangle((5, height - 42, width - 5, height - 5), fill="white")
    draw.text(
        (10, height - 36),
        "Projective rectification for normalized vent comparison only; X=27.5 mm, Y=41.5 mm.",
        fill=(150, 0, 0),
        font=font,
    )
    return rectified


def annotate_cross_section(page_render_path: Path) -> Image.Image:
    if sha256(page_render_path) != EXPECTED_PAGE_RENDER_SHA256:
        raise SystemExit("300 dpi page-render hash mismatch")
    page = Image.open(page_render_path).convert("RGB")
    if page.size != EXPECTED_PAGE_RENDER_SIZE:
        raise ValueError(f"Expected page render {EXPECTED_PAGE_RENDER_SIZE}, got {page.size}")
    crop = page.crop(CROSS_SECTION_CROP)
    draw = ImageDraw.Draw(crop)
    font = label_font(22)
    draw.rectangle((2225, 145, 2385, 285), outline=(220, 0, 0), width=4)
    draw.line((2305, 285, 2190, 360), fill=(220, 0, 0), width=4)
    draw.rectangle((1670, 350, 2390, 395), fill="white", outline=(220, 0, 0), width=2)
    draw.text((1682, 360), "Only dimensional claim here: total 2.8 mm", fill=(180, 0, 0), font=font)
    draw.rectangle((410, 145, 1695, 282), outline=(220, 0, 0), width=3)
    draw.line((1050, 282, 1050, 350), fill=(220, 0, 0), width=4)
    draw.rectangle((660, 350, 1450, 395), fill="white", outline=(220, 0, 0), width=2)
    draw.text((675, 360), "Qualitative membrane/jet topology only", fill=(180, 0, 0), font=font)
    draw.rectangle((5, crop.height - 47, crop.width - 5, crop.height - 5), fill="white", outline=(180, 0, 0), width=2)
    draw.text(
        (12, crop.height - 40),
        "Schematic cross-section: do not scale internal layers, count green waves, or infer cell boundaries.",
        fill=(160, 0, 0),
        font=font,
    )
    return crop


def write_corner_csv(path: Path) -> None:
    rows = []
    labels = ("rear_left", "rear_right", "outlet_right", "outlet_left")
    for index, (label, point) in enumerate(zip(labels, SOURCE_TOP_QUAD)):
        rows.append(
            {
                "figure_id": "GEN1_TOP_RENDER_OBJECT_006",
                "point_id": f"Q{index}",
                "meaning": label,
                "x_px": f"{point[0]:.1f}",
                "y_px": f"{point[1]:.1f}",
                "selection_uncertainty_px": f"{CORNER_UNCERTAINTY_PX:.1f}",
                "evidence_class": "I",
                "allowed_use": "projective_rectification_and_normalized_vent_comparison",
                "forbidden_use": "manufacturing_tolerance_or_internal_cell_count",
            }
        )
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_measurement_csv(path: Path) -> None:
    fields = [
        "measurement_id",
        "figure_id",
        "source_pdf_sha256",
        "source_locator",
        "feature",
        "evidence_class",
        "x0_mm_rectified",
        "y0_mm_rectified",
        "x1_mm_rectified",
        "y1_mm_rectified",
        "reported_value",
        "unit",
        "image_readout_uncertainty",
        "model_form_uncertainty",
        "allowed_use",
        "forbidden_use",
    ]
    rows: list[dict[str, object]] = []
    for name, (x0, y0, x1, y1) in VENT_BOUNDS_MM.items():
        rows.append(
            {
                "measurement_id": name.split("_")[0],
                "figure_id": "GEN1_TOP_RENDER_OBJECT_006",
                "source_pdf_sha256": SOURCE_PDF_SHA256,
                "source_locator": "page 1 upper product render; pdfimages RGB object 006 plus soft mask 007",
                "feature": name,
                "evidence_class": "I",
                "x0_mm_rectified": f"{x0:.2f}",
                "y0_mm_rectified": f"{y0:.2f}",
                "x1_mm_rectified": f"{x1:.2f}",
                "y1_mm_rectified": f"{y1:.2f}",
                "reported_value": "",
                "unit": "mm_after_projective_rectification",
                "image_readout_uncertainty": f"+/-{VENT_READOUT_UNCERTAINTY_MM:.2f} mm",
                "model_form_uncertainty": "stylized marketing render; second-view center shift reaches millimeter scale (up to about 2.6 mm)",
                "allowed_use": "candidate top-cover vent placement and normalized layout comparison",
                "forbidden_use": "manufacturing tolerance, internal cell count, membrane dimensions",
            }
        )
    qualitative = (
        ("CS01", "multiple vibrating membranes", "D", "present", "topology only"),
        ("CS02", "pulsating jets directed toward heat-spreader channel", "D", "present", "flow topology only"),
        ("CS03", "single-side integrated spout/exhaust direction", "D", "present", "flow topology only"),
        ("CS04", "heat spreader below jet channel and above processor", "D", "present", "stack order only"),
        ("CS05", "total module thickness", "D", "2.8", "metric table and figure label"),
        ("CS06", "internal layer and cavity thickness proportions", "U", "", "schematic; not dimensionable"),
    )
    for identifier, feature, evidence_class, value, note in qualitative:
        rows.append(
            {
                "measurement_id": identifier,
                "figure_id": "GEN1_OFFICIAL_CROSS_SECTION",
                "source_pdf_sha256": SOURCE_PDF_SHA256,
                "source_locator": "page 1 cross section of AirJet module",
                "feature": feature,
                "evidence_class": evidence_class,
                "x0_mm_rectified": "",
                "y0_mm_rectified": "",
                "x1_mm_rectified": "",
                "y1_mm_rectified": "",
                "reported_value": value,
                "unit": "mm" if identifier == "CS05" else "qualitative",
                "image_readout_uncertainty": "not applicable" if identifier != "CS05" else "as reported",
                "model_form_uncertainty": note,
                "allowed_use": "product topology and total-envelope constraint",
                "forbidden_use": "scaled internal thicknesses or green-wave cell count",
            }
        )
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rgb", type=Path, required=True)
    parser.add_argument("--mask", type=Path, required=True)
    parser.add_argument("--page-render", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    if sha256(args.rgb) != EXPECTED_RGB_SHA256:
        raise SystemExit("RGB object hash mismatch")
    if sha256(args.mask) != EXPECTED_MASK_SHA256:
        raise SystemExit("Soft-mask hash mismatch")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    composited = load_composited(args.rgb, args.mask)
    annotate_source(composited).save(args.out_dir / "gen1_top_render_quad_annotated.png")
    rectify(composited).save(args.out_dir / "gen1_top_render_rectified.png")
    annotate_cross_section(args.page_render).save(args.out_dir / "gen1_cross_section_annotated.png")
    write_corner_csv(args.out_dir / "gen1_top_render_corner_coordinates.csv")
    write_measurement_csv(args.out_dir.parent / "official_image_measurements.csv")
    print(f"PASS out_dir={args.out_dir}")


if __name__ == "__main__":
    main()
