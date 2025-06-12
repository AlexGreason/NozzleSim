import os
import sys
import math

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import helperfuncs as h


def test_machangle():
    assert math.isclose(h.machangle(2), math.asin(0.5))


def test_binarysearch():
    val = h.binarysearch(0, 10, 9, 20, lambda x: x * x)
    assert math.isclose(val, 3, rel_tol=1e-4)


def test_calcshockemitangle_manual():
    gamma = 1.25
    angle = 10
    mach1 = 1.5
    mach2 = h.calcmach(gamma, mach1, abs(angle))
    alpha1 = math.degrees(h.machangle(mach1))
    alpha2 = math.degrees(h.machangle(mach2))
    expected = (alpha1 + alpha2) / 2 + 0.5 * abs(angle)
    assert math.isclose(h.calcshockemitangle(gamma, angle, mach1=mach1), expected)


def test_alphadiff_symmetry():
    gamma = 1.4
    diff1 = h.alphadiff(gamma, 10, 20)
    diff2 = h.alphadiff(gamma, 20, 10)
    assert math.isclose(diff1 + diff2, 0, abs_tol=1e-9)


def test_area_ratio_and_inverse():
    gamma = 1.4
    mach = 2.0
    ratio = h.calcarearatio(gamma, mach)
    computed = h.calcmachfromarearatio(gamma, ratio)
    assert math.isclose(computed, mach, rel_tol=1e-4)


def test_shockangle_and_prop():
    gamma = 1.4
    v = 10
    theta = 20
    turning = 5
    angle = h.shockangle(gamma, v, theta, turning)
    mach1 = h.calcmach(gamma, 1, v)
    alpha1 = math.degrees(h.machangle(mach1))
    assert math.isclose(angle, -alpha1 + theta)
    prop = h.shockprop(gamma, v, theta, turning)
    angle2 = h.shockangle(gamma, v + abs(turning), theta + turning, turning)
    expected_prop = (angle + angle2) / 2
    assert math.isclose(prop, expected_prop)
