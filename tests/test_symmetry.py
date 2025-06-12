import os
import sys

import numpy as np

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nozzlesim import Wall, Point, Mesh, Shock


def check_symmetry(mesh, epsilon=1e-4):
    any_failed = False
    for seg in mesh.shocks:
        matchfound = False
        closestmatch = float("inf")
        for seg2 in mesh.shocks:
            if (
                abs(seg.start.x - seg2.start.x) < epsilon
                and abs(seg.start.y + seg2.start.y) < epsilon
                and abs(seg.angle + seg2.angle) < epsilon
            ):
                matchfound = True
                break
            closestmatch = min(
                closestmatch,
                np.sqrt(
                    (seg.start.x - seg2.start.x) ** 2
                    + (seg.start.y + seg2.start.y) ** 2
                )
                + (seg.angle + seg2.angle) ** 2,
            )
        if not matchfound:
            parameters = [
                (seg.start.x, seg.start.y) if seg.start is not None else (),
                (seg.end.x, seg.end.y) if seg.end is not None else (),
                seg.angle,
            ]
            print(f"Symmetry break: {parameters}, closest match: {closestmatch:.4f}")
            any_failed = True
    return any_failed


def test_symmetry():
    for n in [1, 2, 3, 4]:
        theta = 10
        topwalls, endx = Wall.createarc(Point(0, 0.5), 0.07, theta, n)
        bottomwalls, endx = Wall.createarc(Point(0, -0.5), 0.07, -theta, n)
        for i in range(len(topwalls)):
            assert (
                abs(topwalls[i].angle + bottomwalls[i].angle) < 1e-4
            ), f"Angle mismatch at index {i}: {topwalls[i].angle} vs {-bottomwalls[i].angle}  "
            assert (
                abs(topwalls[i].start.x - bottomwalls[i].start.x) < 1e-4
            ), f"Start x mismatch at index {i}: {topwalls[i].start.x} vs {bottomwalls[i].start.x}  "
            assert (
                abs(topwalls[i].start.y + bottomwalls[i].start.y) < 1e-4
            ), f"Start y mismatch at index {i}: {topwalls[i].start.y} vs {-bottomwalls[i].start.y}  "
        mesh = Mesh(1.25, 1, [], topwalls + bottomwalls, endx, 1)
        mesh.simulate()
        table = mesh.getxytable(0, 1000, 0.011)
        assert not check_symmetry(
            mesh, epsilon=1e-3
        ), f"Symmetry check failed for n={n} and theta={theta} degrees"
        assert (
            len(list(x for x in mesh.activeshocks if isinstance(x, Shock))) == 0
        ), f"Active shock found after simulation for n={n} and theta={theta} degrees"
