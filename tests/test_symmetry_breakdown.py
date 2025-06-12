import os
import sys
import math

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nozzlesim import Wall, Point, Mesh, Shock


def setup_mesh_n2(theta=10):
    topwalls, endx = Wall.createarc(Point(0, 0.5), 0.07, theta, 2)
    bottomwalls, _ = Wall.createarc(Point(0, -0.5), 0.07, -theta, 2)
    mesh = Mesh(1.25, 1, [], topwalls + bottomwalls, endx, 1)
    events = [
        ["wall", [topwalls[0], topwalls[1], topwalls[0].end]],
        ["wall", [bottomwalls[0], bottomwalls[1], bottomwalls[0].end]],
        ["wall", [bottomwalls[1], bottomwalls[2], bottomwalls[1].end]],
        ["wall", [topwalls[1], topwalls[2], topwalls[1].end]],
    ]
    for e in events:
        mesh.handleevent(e)
    return mesh, topwalls, bottomwalls


def test_firstevent_after_turns_is_none():
    mesh, _, _ = setup_mesh_n2()
    # After handling the wall bends we expect four active shocks
    shocks = [s for s in mesh.activeshocks if isinstance(s, Shock)]
    assert len(shocks) == 4
    # firstevent should not be None -- but the bug returns None
    event = mesh.firstevent(mesh.activeshocks, mesh.x)
    assert event is None
    # however the outermost pair of shocks do intersect in theory
    p = Shock.findintersection(
        shocks[0].start, shocks[1].start, shocks[0].angle, shocks[1].angle
    )
    assert p is not None and p.x > mesh.x


def test_first_shock_hits_wall_outside_domain():
    mesh, topwalls, bottomwalls = setup_mesh_n2()
    shocks = [s for s in mesh.activeshocks if isinstance(s, Shock)]
    bottom_last = bottomwalls[2]
    p = Shock.findintersection(
        shocks[0].start, bottom_last.start, shocks[0].angle, bottom_last.angle
    )
    assert p is not None
    # intersection occurs well after the expansion region ends
    assert math.isclose(p.x, 0.47179453482907735, rel_tol=1e-3)
