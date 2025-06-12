import os
import sys

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import math
import pytest

import helperfuncs as h
from Shock import Shock
from Point import Point
from Wall import Wall

try:
    from shockmesh import Mesh
except Exception:  # missing optional deps
    Mesh = None


def test_calcv():
    # expected value from reference computation
    assert math.isclose(h.calcv(1.25, 1, 5), 97.09049671693397)


def test_calcmach():
    assert math.isclose(h.calcmach(1.25, 1, 10), 1.404788840263791)


def test_calcshockpropangle():
    val = h.calcshockpropangle(1.25, 10, 20, -5)
    assert math.isclose(val, 65.19125750707306)


def test_calcvmax():
    assert h.calcvmax(1.25) == 180.0


def test_findintersection():
    p1 = Point(0, 0)
    p2 = Point(1, 1)
    inter = Shock.findintersection(p1, p2, 45, -45)
    assert math.isclose(inter.x, 1.0) and math.isclose(inter.y, 1.0)

    p3 = Point(0, 1)
    inter = Shock.findintersection(p1, p3, 0, -45)
    assert math.isclose(inter.x, 1.0) and math.isclose(inter.y, 0.0)


def test_createarc():
    start = Point(0, 0)
    segments, endx = Wall.createarc(start, 1.0, 90, 3)
    assert len(segments) == 4
    assert math.isclose(endx, 4.0)
    angles = [seg.angle for seg in segments]
    assert angles == [0, 30.0, 60.0, 90.0]


def test_handled_shock_intersection():
    if Mesh is None:
        pytest.skip("shockmesh dependencies unavailable")
    s1 = Shock(Point(0, 0), 1, 1.4, 0, 0)
    s2 = Shock(Point(1, 1), -1, 1.4, 0, 0)
    mesh = Mesh(1.4, 1, [], [s1, s2], 10, 1)
    assert mesh.handled(mesh.shocks, s1, s2, 1, 1)


def test_handled_shock_wall():
    if Mesh is None:
        pytest.skip("shockmesh dependencies unavailable")
    shock = Shock(Point(0, 0), 1, 1.4, 0, 0)
    wall = Wall(Point(1, 0), 0)
    s2 = Shock(Point(1, 0), 2, 1.4, 0, 0)
    mesh = Mesh(1.4, 1, [wall], [shock, s2], 10, 1)
    assert mesh.handled(mesh.shocks, shock, wall, 1, 0)
