import os
import sys
import math

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

import helperfuncs as h
from reference_cases import manual_prop_angle

CASES = [
    dict(gamma=1.4, M1=2.0, theta=0.0, delta=-5.0),
    dict(gamma=1.4, M1=3.0, theta=0.0, delta=10.0),
    dict(gamma=1.4, M1=2.0, theta=15.0, delta=-3.0),
]


@pytest.mark.parametrize("case", CASES)
def test_reference_case_angles(case):
    gamma = case['gamma']
    v1 = h.calcv(gamma, 1, case['M1'])
    theta = case['theta']
    delta = case['delta']
    code_angle = h.shockprop(gamma, v1, theta, delta)
    manual_angle = manual_prop_angle(gamma, v1, theta, delta)
    assert math.isclose(code_angle, manual_angle, rel_tol=1e-6)
