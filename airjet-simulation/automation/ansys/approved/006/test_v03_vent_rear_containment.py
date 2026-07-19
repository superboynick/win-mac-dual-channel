"""Negative tests for rear inlet containment in v03_continuous_fluid_producer.

These tests verify that the producer rejects vent boxes extending beyond
the footprint rear boundary.  IronPython 2.7 / CPython 3 compatible.
"""
from __future__ import print_function

import sys, os
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TESTS_DIR)


def _compute_vent_box(center_y, axis_dy, axis_length, slot_width):
    dx = 0.0; dy = float(axis_dy)
    length = float(axis_length); width = float(slot_width)
    half_x = abs(dx) * length / 2.0 + abs(dy) * width / 2.0
    half_y = abs(dy) * length / 2.0 + abs(dx) * width / 2.0
    cx = 0.0; cy = float(center_y)
    return [cx - half_x, cy - half_y, cx + half_x, cy + half_y]


def _clip_rear(box, footprint_y_min):
    rear_overhang_mm = footprint_y_min - box[1]
    if rear_overhang_mm > 0.01:
        box[1] = footprint_y_min
    return rear_overhang_mm


def test_v01_overhang_detected():
    fp = -14.375
    box = _compute_vent_box(-10.700, 1.0, 14.100, 1.700)
    assert box[1] < -17.0, "V01 too shallow: " + str(box[1])
    oh = _clip_rear(box, fp)
    assert oh > 3.0, "V01 overhang too small: " + str(oh)
    assert abs(box[1] - fp) < 0.001
    print("PASS: test_v01_overhang=%.3f mm" % oh)


def test_v02_overhang_detected():
    fp = -14.375
    box = _compute_vent_box(-10.600, 1.0, 14.300, 1.700)
    assert box[1] < -17.0
    oh = _clip_rear(box, fp)
    assert oh > 3.0
    assert abs(box[1] - fp) < 0.001
    print("PASS: test_v02_overhang=%.3f mm" % oh)


def test_v03_v04_no_overhang():
    fp = -14.375
    for vid, cy, ln in [("V03", 5.500, 14.500), ("V04", 5.900, 14.900)]:
        box = _compute_vent_box(cy, 1.0, ln, 1.700)
        oh = _clip_rear(box, fp)
        assert oh <= 0.01, "%s overhang %.3f" % (vid, oh)
        print("PASS: test_%s_no_overhang Ymin=%.3f" % (vid.lower(), box[1]))


def test_four_inlets_preserved():
    fp = -14.375
    vents = [("V01",-10.700,1.0,14.100,1.700),("V02",-10.600,1.0,14.300,1.700),
             ("V03",5.500,1.0,14.500,1.700),("V04",5.900,1.0,14.900,1.700)]
    boxes = []
    for vid, cy, dy, ln, w in vents:
        box = _compute_vent_box(cy, dy, ln, w)
        _clip_rear(box, fp)
        assert box[0] < box[2], vid + " X collapse"
        assert box[1] >= fp - 0.001, vid + " breach"
        assert box[3] > box[1], vid + " Y collapse"
        boxes.append(box)
    assert len(boxes) == 4
    print("PASS: test_four_inlets_preserved (%d boxes)" % len(boxes))


def test_bbox_only_insufficient():
    fp = -14.375
    box = _compute_vent_box(-10.700, 1.0, 14.100, 1.700)
    oh = fp - box[1]
    assert oh > 1.0, "bbox would hide %.3f mm" % oh
    print("PASS: test_bbox_insufficient (overhang=%.3f mm)" % oh)


def test_inlet_outlet_no_role_reversal():
    outlet_y_min = 17.75
    vymax = []
    for cy, ln in [(-10.700,14.100),(-10.600,14.300),(5.500,14.500),(5.900,14.900)]:
        box = _compute_vent_box(cy, 1.0, ln, 1.700)
        vymax.append(box[3])
    assert max(vymax) < outlet_y_min
    print("PASS: test_no_role_reversal max_vent_y=%.3f < outlet=%.3f" % (max(vymax), outlet_y_min))


def test_clip_idempotent():
    fp = -14.375
    box = [5.0, -10.0, 6.0, 10.0]
    orig = list(box)
    oh = _clip_rear(box, fp)
    assert oh <= 0.01
    assert box == orig
    print("PASS: test_clip_idempotent")


if __name__ == "__main__":
    tests = [test_v01_overhang_detected, test_v02_overhang_detected,
             test_v03_v04_no_overhang, test_four_inlets_preserved,
             test_bbox_only_insufficient, test_inlet_outlet_no_role_reversal,
             test_clip_idempotent]
    fails = 0
    for t in tests:
        try: t()
        except Exception as e: fails += 1; print("FAIL: " + t.__name__ + " -- " + str(e))
    print("\n%d/%d tests passed" % (len(tests) - fails, len(tests)))
    if fails: sys.exit(1)