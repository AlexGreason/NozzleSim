import os
import sys
import math

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

import nozzlesim.helperfuncs as h


def manual_prop_angle(gamma, v1, theta, delta):
    """Return expected propagation angle of a characteristic after a bend."""
    M1 = h.calcmach(gamma, 1, v1)
    v2 = v1 + abs(delta)
    M2 = h.calcmach(gamma, 1, v2)
    mu1 = math.degrees(math.asin(1 / M1))
    mu2 = math.degrees(math.asin(1 / M2))
    theta1 = theta
    theta2 = theta + delta
    sign = 1 if delta < 0 else -1
    return (theta1 + theta2) / 2 + sign * (mu1 + mu2) / 2


CASES = [
    dict(gamma=1.4, M1=2.0, theta=0.0, delta=-5.0),
    dict(gamma=1.4, M1=3.0, theta=0.0, delta=10.0),
    dict(gamma=1.4, M1=2.0, theta=15.0, delta=-3.0),
]


@pytest.mark.parametrize("case", CASES)
def test_reference_case_angles(case):
    gamma = case["gamma"]
    v1 = h.calcv(gamma, 1, case["M1"])
    theta = case["theta"]
    delta = case["delta"]
    code_angle = h.shockprop(gamma, v1, theta, delta)
    manual_angle = manual_prop_angle(gamma, v1, theta, delta)
    assert math.isclose(code_angle, manual_angle, rel_tol=1e-6)
