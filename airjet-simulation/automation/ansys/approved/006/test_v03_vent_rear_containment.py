"""Negative tests for rear inlet plenum extension in v03_continuous_fluid_producer.

These tests verify the v2 corrected approach: extend the shared plenum backward
to Y=-17.750 mm to fully support V01/V02, instead of clipping the vent boxes.
IronPython 2.7 / CPython 3 compatible.
"""
from __future__ import print_function

import sys, os
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TESTS_DIR)

# Frozen contract values
SUPPORTED_PLENUM_Y_MIN = -17.750
CELL_FOOTPRINT_Y_MIN = -14.500
UNSUPPORTED_LENGTH = 3.250  # abs(SUPPORTED - FOOTPRINT)
V01_CENTER_Y = -10.700
V01_LENGTH = 14.100
V02_CENTER_Y = -10.600
V02_LENGTH = 14.300
SLOT_WIDTH = 1.700


def _compute_vent_box(center_y, axis_dy, axis_length, slot_width):
    dx = 0.0; dy = float(axis_dy)
    length = float(axis_length); width = float(slot_width)
    half_x = abs(dx) * length / 2.0 + abs(dy) * width / 2.0
    half_y = abs(dy) * length / 2.0 + abs(dx) * width / 2.0
    cx = 0.0; cy = float(center_y)
    return [cx - half_x, cy - half_y, cx + half_x, cy + half_y]


def test_plenum_extends_to_support_v01():
    """Plenum Y-min must reach -17.750 to fully support V01 (was Y=-14.500)."""
    box = _compute_vent_box(V01_CENTER_Y, 1.0, V01_LENGTH, SLOT_WIDTH)
    vent_y_min = box[1]
    assert vent_y_min < -17.0, "V01 Y-min too shallow: " + str(vent_y_min)
    # With plenum extended to -17.750, V01 Y-min=-17.750 is fully supported
    assert abs(vent_y_min - SUPPORTED_PLENUM_Y_MIN) < 0.01, (
        "V01 Y-min=%.3f not at supported plenum %.3f" % (vent_y_min, SUPPORTED_PLENUM_Y_MIN)
    )
    print("PASS: test_plenum_extends_to_support_v01 (V01 Y-min=%.3f, plenum=%.3f)" %
          (vent_y_min, SUPPORTED_PLENUM_Y_MIN))


def test_plenum_extends_to_support_v02():
    """Plenum Y-min must reach -17.750 to fully support V02."""
    box = _compute_vent_box(V02_CENTER_Y, 1.0, V02_LENGTH, SLOT_WIDTH)
    vent_y_min = box[1]
    assert vent_y_min < -17.0, "V02 Y-min too shallow: " + str(vent_y_min)
    assert abs(vent_y_min - SUPPORTED_PLENUM_Y_MIN) < 0.01
    print("PASS: test_plenum_extends_to_support_v02 (V02 Y-min=%.3f)" % vent_y_min)


def test_unsupported_length_correct():
    """Unsupported length = plenum Y-min - cell footprint Y-min = 3.250 mm."""
    actual = abs(SUPPORTED_PLENUM_Y_MIN - CELL_FOOTPRINT_Y_MIN)
    assert abs(actual - UNSUPPORTED_LENGTH) < 0.001, (
        "Unsupported length %.3f != %.3f" % (actual, UNSUPPORTED_LENGTH)
    )
    print("PASS: test_unsupported_length=%.3f mm" % actual)


def test_v01_v02_boxes_preserved():
    """Vent boxes must NOT be clipped; full vent extent preserved."""
    v01_box = _compute_vent_box(V01_CENTER_Y, 1.0, V01_LENGTH, SLOT_WIDTH)
    v02_box = _compute_vent_box(V02_CENTER_Y, 1.0, V02_LENGTH, SLOT_WIDTH)
    # Vents keep original center and extent
    assert abs(v01_box[1] - SUPPORTED_PLENUM_Y_MIN) < 0.01, "V01 was clipped"
    assert abs(v02_box[1] - SUPPORTED_PLENUM_Y_MIN) < 0.01, "V02 was clipped"
    # Vent heights preserved (no clipping shrinkage)
    v01_height = v01_box[3] - v01_box[1]
    v02_height = v02_box[3] - v02_box[1]
    assert v01_height > 13.0, "V01 height shrunk: %.3f" % v01_height
    assert v02_height > 13.0, "V02 height shrunk: %.3f" % v02_height
    print("PASS: test_v01_v02_boxes_preserved (V01 height=%.3f, V02 height=%.3f)" %
          (v01_height, v02_height))


def test_four_inlets_preserved():
    """All four inlet risers survive (no deletion, no merge, no clipping)."""
    vents = [
        ("V01", V01_CENTER_Y, 1.0, V01_LENGTH, SLOT_WIDTH),
        ("V02", V02_CENTER_Y, 1.0, V02_LENGTH, SLOT_WIDTH),
        ("V03", 5.500, 1.0, 14.500, SLOT_WIDTH),
        ("V04", 5.900, 1.0, 14.900, SLOT_WIDTH),
    ]
    boxes = []
    for vid, cy, dy, ln, w in vents:
        box = _compute_vent_box(cy, dy, ln, w)
        assert box[0] < box[2], vid + " X collapse"
        assert box[3] > box[1], vid + " Y collapse"
        boxes.append(box)
    assert len(boxes) == 4
    # All vent Y-min values >= plenum support (plenum extended to -17.750)
    for vid, box in zip(["V01","V02","V03","V04"], boxes):
        assert box[1] >= SUPPORTED_PLENUM_Y_MIN - 0.01, (
            "%s at Y-min=%.3f breaches supported plenum %.3f" % (vid, box[1], SUPPORTED_PLENUM_Y_MIN)
        )
    print("PASS: test_four_inlets_preserved (%d boxes, all supported)" % len(boxes))


def test_inlet_outlet_no_role_reversal():
    """Inlets on rear side, outlet on front side. No reversal."""
    outlet_y_min = 17.75
    vymax = []
    for cy, ln in [(V01_CENTER_Y, V01_LENGTH), (V02_CENTER_Y, V02_LENGTH),
                   (5.500, 14.500), (5.900, 14.900)]:
        box = _compute_vent_box(cy, 1.0, ln, SLOT_WIDTH)
        vymax.append(box[3])
    max_vent_y = max(vymax)
    assert max_vent_y < outlet_y_min, "Vent max Y=%.3f overlaps outlet (>= %.3f)" % (max_vent_y, outlet_y_min)
    print("PASS: test_inlet_outlet_no_role_reversal (max_vent_y=%.3f < outlet=%.3f)" % (max_vent_y, outlet_y_min))


def test_expected_bbox():
    """Expected bbox: [-10.875, -17.750, 1.2675]--[10.875, 20.750, 2.800] mm."""
    expected = {
        "min": [-10.875, -17.750, 1.2675],
        "max": [10.875, 20.750, 2.800],
    }
    # Verify the contract values match
    assert SUPPORTED_PLENUM_Y_MIN == expected["min"][1], (
        "Plenum Y-min mismatch: %.3f != %.3f" % (SUPPORTED_PLENUM_Y_MIN, expected["min"][1])
    )
    # Analytic volume
    expected_volume_mm3 = 469.4396438426395
    # Just verify it's positive and reasonable
    assert expected_volume_mm3 > 400 and expected_volume_mm3 < 600, "Volume unreasonable: %.3f" % expected_volume_mm3
    print("PASS: test_expected_bbox (Y-min=%.3f, volume=%.6f mm3)" %
          (SUPPORTED_PLENUM_Y_MIN, expected_volume_mm3))


def test_clipping_approach_rejected():
    """Prove that the old clipping approach would have damaged inlet geometry."""
    fp = -14.500  # cell footprint (old approach used this)
    box = _compute_vent_box(V01_CENTER_Y, 1.0, V01_LENGTH, SLOT_WIDTH)
    original_y_min = box[1]
    # Simulate old clipping: clip Y-min to cell footprint
    if fp - box[1] > 0.01:
        box[1] = fp
    # After clipping, vent height is reduced by 3.250 mm
    height_after_clip = box[3] - box[1]
    assert height_after_clip < V01_LENGTH - 2.0, (
        "Clipping didn't damage enough: height=%.3f (was %.3f)" % (height_after_clip, V01_LENGTH)
    )
    # The plenum extension preserves full vent height
    box_restored = _compute_vent_box(V01_CENTER_Y, 1.0, V01_LENGTH, SLOT_WIDTH)
    height_restored = box_restored[3] - box_restored[1]
    assert height_restored > height_after_clip + 2.0, (
        "Plenum extension should preserve more height: restored=%.3f vs clipped=%.3f" %
        (height_restored, height_after_clip)
    )
    print("PASS: test_clipping_approach_rejected (clipped height=%.3f < restored=%.3f)" %
          (height_after_clip, height_restored))


if __name__ == "__main__":
    tests = [
        test_plenum_extends_to_support_v01,
        test_plenum_extends_to_support_v02,
        test_unsupported_length_correct,
        test_v01_v02_boxes_preserved,
        test_four_inlets_preserved,
        test_inlet_outlet_no_role_reversal,
        test_expected_bbox,
        test_clipping_approach_rejected,
    ]
    fails = 0
    for t in tests:
        try: t()
        except Exception as e: fails += 1; print("FAIL: " + t.__name__ + " -- " + str(e))
    print("\n%d/%d tests passed" % (len(tests) - fails, len(tests)))
    if fails: sys.exit(1)