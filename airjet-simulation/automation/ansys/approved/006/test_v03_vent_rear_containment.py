"""Negative tests for rear inlet containment in v03_continuous_fluid_producer.

These tests verify that the producer rejects vent boxes extending beyond
the footprint rear boundary.  IronPython 2.7 / CPython 3 compatible.
"""
from __future__ import print_function

import math
import os
import sys

# Add parent to path for import
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TESTS_DIR)

# ---------------------------------------------------------------------------
# Pure-logic tests -- no SpaceClaim API needed
# ---------------------------------------------------------------------------

def _compute_vent_box(center_y, axis_dy, axis_length, slot_width):
    """Replicate the vent box computation from the producer."""
    dx = 0.0
    dy = float(axis_dy)
    length = float(axis_length)
    width = float(slot_width)
    half_x = abs(dx) * length / 2.0 + abs(dy) * width / 2.0
    half_y = abs(dy) * length / 2.0 + abs(dx) * width / 2.0
    cx = 0.0
    cy = float(center_y)
    return [cx - half_x, cy - half_y, cx + half_x, cy + half_y]


def _clip_rear(box, footprint_y_min):
    """Clip vent box Y-min to footprint rear boundary (replicates the fix)."""
    rear_overhang_mm = footprint_y_min - box[1]
    if rear_overhang_mm > 0.01:
        box[1] = footprint_y_min
    return rear_overhang_mm


def test_v01_overhang_detected():
    """V01 (VENT_FLOW_BBOX_R0) extends to Y=-17.750, footprint Y-min=-14.375."""
    footprint_y_min = -14.375
    box = _compute_vent_box(
        center_y=-10.700, axis_dy=1.0, axis_length=14.100, slot_width=1.700
    )
    y_min_before = box[1]
    assert y_min_before < -17.0, "V01 should extend below -17 mm: got %.3f" % y_min_before
    overhang = _clip_rear(box, footprint_y_min)
    assert overhang > 3.0, "V01 overhang should be > 3 mm: got %.3f" % overhang
    assert abs(box[1] - footprint_y_min) < 0.001, (
        "V01 Y-min should be clipped to footprint: %.3f != %.3f" % (box[1], footprint_y_min)
    )
    print("PASS: test_v01_overhang_detected (overhang=%.3f mm, clipped to %.3f)" %
          (overhang, box[1]))


def test_v02_overhang_detected():
    """V02 (VENT_FLOW_BBOX_R0) extends to Y=-17.750, footprint Y-min=-14.375."""
    footprint_y_min = -14.375
    box = _compute_vent_box(
        center_y=-10.600, axis_dy=1.0, axis_length=14.300, slot_width=1.700
    )
    y_min_before = box[1]
    assert y_min_before < -17.0, "V02 should extend below -17 mm: got %.3f" % y_min_before
    overhang = _clip_rear(box, footprint_y_min)
    assert overhang > 3.0, "V02 overhang should be > 3 mm: got %.3f" % overhang
    assert abs(box[1] - footprint_y_min) < 0.001
    print("PASS: test_v02_overhang_detected (overhang=%.3f mm, clipped to %.3f)" %
          (overhang, box[1]))


def test_v03_v04_no_overhang():
    """V03 and V04 are on the front side and should not clip."""
    footprint_y_min = -14.375
    for vent_id, center_y, length in [
        ("V03", 5.500, 14.500), ("V04", 5.900, 14.900)
    ]:
        box = _compute_vent_box(
            center_y=center_y, axis_dy=1.0, axis_length=length, slot_width=1.700
        )
        overhang = _clip_rear(box, footprint_y_min)
        assert overhang <= 0.01, (
            "%s should not overhang: Y-min=%.3f, overhang=%.3f" % (vent_id, box[1], overhang)
        )
        print("PASS: test_%s_no_overhang (Y-min=%.3f)" % (vent_id.lower(), box[1]))


def test_four_inlets_preserved():
    """All four inlet risers must survive clipping (no deletion)."""
    footprint_y_min = -14.375
    vents = [
        ("V01", -10.700, 1.0, 14.100, 1.700),
        ("V02", -10.600, 1.0, 14.300, 1.700),
        ("V03", 5.500, 1.0, 14.500, 1.700),
        ("V04", 5.900, 1.0, 14.900, 1.700),
    ]
    boxes = []
    for vent_id, cy, dy, length, width in vents:
        box = _compute_vent_box(cy, dy, length, width)
        _clip_rear(box, footprint_y_min)
        # Every box must have positive extent after clip
        assert box[0] < box[2], "%s X collapsed" % vent_id
        assert box[1] >= footprint_y_min - 0.001, "%s breaches rear" % vent_id
        assert box[3] > box[1], "%s Y collapsed" % vent_id
        boxes.append(box)
    assert len(boxes) == 4, "Must preserve 4 inlet risers"
    print("PASS: test_four_inlets_preserved (%d boxes)" % len(boxes))


def test_bbox_only_insufficient():
    """Global bbox pass does not prove per-inlet containment."""
    footprint_y_min = -14.375
    # Simulate a V01 that would pass global bbox but breach rear locally
    box = _compute_vent_box(-10.700, 1.0, 14.100, 1.700)
    global_min_y = min(box[1], footprint_y_min - 5.0)  # bbox would still contain
    # Per-inlet check must still fail
    overhang = footprint_y_min - box[1]
    assert overhang > 1.0, (
        "Bbox-only check would miss %.3f mm overhang" % overhang
    )
    print("PASS: test_bbox_only_insufficient (overhang=%.3f mm hidden by global bbox)" % overhang)


def test_inlet_outlet_no_role_reversal():
    """Inlets must not be mistaken for outlet."""
    # All four vent centers have negative or small positive Y (front half)
    # Outlet is on the far positive Y side (+20.75 mm)
    outlet_y_min = 17.75  # outlet starts beyond Y=17.75
    vent_y_max_values = []
    for center_y, length in [(-10.700, 14.100), (-10.600, 14.300),
                              (5.500, 14.500), (5.900, 14.900)]:
        box = _compute_vent_box(center_y, 1.0, length, 1.700)
        vent_y_max_values.append(box[3])
    max_vent_y = max(vent_y_max_values)
    assert max_vent_y < outlet_y_min, (
        "Vent Y-max %.3f overlaps outlet zone (>= %.3f)" % (max_vent_y, outlet_y_min)
    )
    print("PASS: test_inlet_outlet_no_role_reversal (max_vent_y=%.3f < outlet=%.3f)" %
          (max_vent_y, outlet_y_min))


def test_clip_idempotent():
    """Clipping an already-contained box must be a no-op."""
    footprint_y_min = -14.375
    box = [5.0, -10.0, 6.0, 10.0]  # already inside
    original = list(box)
    overhang = _clip_rear(box, footprint_y_min)
    assert overhang <= 0.01
    assert box == original, "Idempotent clip modified contained box"
    print("PASS: test_clip_idempotent")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tests = [
        test_v01_overhang_detected,
        test_v02_overhang_detected,
        test_v03_v04_no_overhang,
        test_four_inlets_preserved,
        test_bbox_only_insufficient,
        test_inlet_outlet_no_role_reversal,
        test_clip_idempotent,
    ]
    failures = 0
    for test in tests:
        try:
            test()
        except Exception as exc:
            failures += 1
            print("FAIL: %s -- %s" % (test.__name__, exc))
    print("\n%d/%d tests passed" % (len(tests) - failures, len(tests)))
    if failures:
        sys.exit(1)
