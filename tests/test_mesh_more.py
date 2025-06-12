import os
import sys
import math

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nozzlesim import Point, Shock, Wall
from nozzlesim.mesh import Mesh, convertpoint


def test_mesh_upstream_and_genwallshock():
    w1 = Wall(Point(0, 0), 0)
    w2 = Wall(Point(1, 0), 0)
    mesh = Mesh(1.4, 2.0, [], [w1, w2], 2, 0)
    vals = mesh.getupstreamvalues(w1)
    assert math.isclose(vals[0], vals[0])  # ensure numbers returned
    new_shock = mesh.genwallshock(w1, w2)
    assert isinstance(new_shock, Shock)
    assert math.isclose(new_shock.turningangle, 0)


def test_mesh_reflect_and_getxytable_convert():
    shock = Shock(Point(0, 0), 5, 1.4, 0, 0)
    reflected = Mesh.reflectshock(shock, 1, 0)
    assert reflected.turningangle == -shock.turningangle
    w = Wall(Point(0, 0), 0)
    mesh = Mesh(1.4, 1.0, [], [w], 1, 0)
    table = mesh.getxytable(0, 3, 0.5)
    assert len(table) == 3
    x, y = convertpoint([(0, 0), (1, 1)], 0.5, 0.5, 100, 100)
    assert math.isclose(x, 50)
    assert math.isclose(y, 50)


def test_findpairs_and_firstevent():
    s1 = Shock(Point(0, 0), 5, 1.4, 0, 0)
    s2 = Shock(Point(0, 1), -5, 1.4, 0, 0)
    # Override automatically computed angles to force an intersection
    s1.angle = 45
    s2.angle = -45
    mesh = Mesh(1.4, 1, [], [s1, s2], 2, 0)
    pair = mesh.firstintersection([s1, s2], 0)
    assert pair[0] in (s1, s2)
    event = mesh.firstevent([s1, s2], 0)
    assert event[0] == "intersection"
    assert isinstance(event[1][2], Point)


def test_handleintersection_and_area():
    s1 = Shock(Point(0, 0), 5, 1.4, 0, 0)
    s2 = Shock(Point(0, 1), -5, 1.4, 0, 0)
    s1.angle = 45
    s2.angle = -45
    mesh = Mesh(1.4, 1, [], [s1, s2], 2, 0)
    mesh.handleintersection(s1, s2, 1, 0.5)
    assert len(mesh.shocks) == 4
    assert s1.end.x == 1 and s2.end.x == 1
    w1 = Wall(Point(0, 0), 0)
    w2 = Wall(Point(0, 1), 0)
    mesh = Mesh(1.4, 1, [], [w1, w2], 1, 0)
    assert math.isclose(mesh.calcarearatio(), 1.0)
