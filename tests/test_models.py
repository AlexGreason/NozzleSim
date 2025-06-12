import os
import sys
import math

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nozzlesim import Point, Shock, Wall
from nozzlesim.mesh import Mesh


def test_point_distance_and_equals():
    p1 = Point(0, 0)
    p2 = Point(3, 4)
    assert p1.distance(p2) == 5
    assert not p1.equals(p2)
    assert p2.equals(Point(3, 4))


def test_shock_vals_and_exists_str():
    shock = Shock(Point(0, 0), 5, 1.4, 0, 0)
    assert shock.getupstreamvals() == [0, 0, 1.4]
    assert shock.getdownstreamvals() == [5, 5, 1.4]
    assert not shock.exists(-1)
    assert shock.exists(0.1)
    shock.end = Point(0.2, 0)
    assert not shock.exists(1)
    text = str(shock)
    assert "Start" in text and "Angle" in text


def test_shock_regions_and_newshocks():
    s1 = Shock(Point(0, 0), 3, 1.4, 0, 0)
    s2 = Shock(Point(1, 0), -2, 1.4, 0, 0)
    params = Shock.calcregionparams(0, 0, 1.4, s1)
    assert params == [3, 3, 1.4]
    new = Shock.newshocks(s1, s2, 1, 1)
    assert len(new) == 2
    assert new[0].turningangle == s2.turningangle
    assert new[1].turningangle == s1.turningangle


def test_wall_methods_and_mesh_helpers():
    wall = Wall(Point(0, 0), 45, Point(1, 1))
    assert wall.propangle() == 45
    assert wall.exists(0.5)
    assert math.isclose(wall.getyposition(0.5), 0.5)
    assert not wall.exists(2)

    other = Wall(Point(1, 1), 45)
    mesh = Mesh(1.4, 1, [], [wall, other], 2, 0)
    sorted_walls = Mesh.sortshocks([wall, other], 0)
    assert sorted_walls[0] == other
    remaining = Mesh.removeended([wall, other], 0.5)
    assert remaining == [wall, other]
    wall.end = Point(0.25, 0.25)
    remaining = Mesh.removeended([wall, other], 0.5)
    assert remaining == [other]


def test_wall_and_mesh_str():
    wall = Wall(Point(0, 0), 0)
    assert "Wall" in str(wall) and "Start" in str(wall)
    mesh = Mesh(1.4, 1.0, [wall], [wall], 1, 0)
    text = str(mesh)
    assert "Mesh(" in text and "Segments:" in text
