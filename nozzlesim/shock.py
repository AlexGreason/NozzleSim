"""Shock/expansion wave utilities."""

from __future__ import annotations

import math
from typing import Iterable, Optional, Sequence, Union

from . import helperfuncs as h
from .point import Point


class Shock:
    """Representation of a single characteristic line."""

    def __init__(
        self,
        start: Union[Point, Sequence[float]],
        turningangle: float,
        gamma: float,
        upstreamv: float,
        upstreamtheta: float,
        end: Optional[Point] = None,
    ) -> None:
        self.start = start if isinstance(start, Point) else Point(start[0], start[1])
        self.turningangle = turningangle
        self.v = upstreamv
        self.theta = upstreamtheta
        self.gamma = gamma
        self.end = end
        self.angle = self.propangle()

    def propangle(self) -> float:
        """Return propagation angle of this characteristic."""

        return h.shockprop(self.gamma, self.v, self.theta, self.turningangle)

    @staticmethod
    def findintersection(
        start1: Point, start2: Point, angle1: float, angle2: float
    ) -> Optional[Point]:
        """Return the intersection point of two rays defined by ``start*`` and ``angle*``."""

        slope1 = math.tan(math.radians(angle1))
        slope2 = math.tan(math.radians(angle2))
        if math.isclose(slope1, slope2):
            return None
        b1 = start1.y - slope1 * start1.x
        b2 = start2.y - slope2 * start2.x
        x = (b2 - b1) / (slope1 - slope2)
        y = slope1 * x + b1
        return Point(x, y)

    def findshockintersection(self, shock2: "Shock") -> Optional[Point]:
        """Intersect this shock with ``shock2``."""

        angle1 = self.propangle()
        angle2 = shock2.propangle()
        return self.findintersection(self.start, shock2.start, angle1, angle2)

    def getupstreamvals(self) -> list[float]:
        """Return ``[v, theta, gamma]`` upstream of the wave."""

        return [self.v, self.theta, self.gamma]

    def getdownstreamvals(self) -> list[float]:
        """Return ``[v, theta, gamma]`` downstream of the wave."""

        return [
            self.v + abs(self.turningangle),
            self.theta + self.turningangle,
            self.gamma,
        ]

    def exists(self, x: float) -> bool:
        """Return ``True`` if ``x`` lies between ``start`` and ``end`` (if defined)."""

        beforestart = x < self.start.x
        afterend = False
        if self.end is not None:
            afterend = x > self.end.x
        return not beforestart and not afterend

    @staticmethod
    def calcregionparams(
        theta: float, v: float, gamma: float, shock: "Shock"
    ) -> list[float]:
        """Return flow parameters in the region downstream of ``shock``."""

        newgamma = gamma
        newtheta = theta + shock.turningangle
        newv = v + abs(shock.turningangle)
        return [newtheta, newv, newgamma]

    @staticmethod
    def newshocks(
        shock1: "Shock", shock2: "Shock", x: float, y: float
    ) -> list["Shock"]:
        """Return new shocks generated when ``shock1`` intersects ``shock2`` at ``(x, y)``."""

        topregion = shock1.calcregionparams(
            shock1.theta, shock1.v, shock1.gamma, shock1
        )
        bottomregion = shock2.calcregionparams(
            shock2.theta, shock2.v, shock2.gamma, shock2
        )
        startpoint = Point(x, y)
        topshock = Shock(
            startpoint, shock2.turningangle, topregion[2], topregion[1], topregion[0]
        )
        bottomshock = Shock(
            startpoint,
            shock1.turningangle,
            bottomregion[2],
            bottomregion[1],
            bottomregion[0],
        )
        return [topshock, bottomshock]

    def __str__(self) -> str:  # pragma: no cover - simple display
        parts = [
            "Shock(",
            f"Start: {self.start}",
            f"Angle: {self.propangle()}",
            f"Turning: {self.turningangle}",
        ]
        if self.end is not None:
            parts.append(f"End: {self.end}")
        return ", ".join(parts) + ")"
