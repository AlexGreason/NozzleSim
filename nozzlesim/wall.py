"""Representation of straight wall segments used in nozzle geometry."""

from __future__ import annotations

import math
from typing import Sequence, Optional, Union

from .point import Point
from .shock import Shock


class Wall:
    """A straight wall segment defined by a start point and angle."""

    def __init__(
        self,
        start: Union[Point, Sequence[float]],
        angle: float,
        end: Optional[Point] = None,
    ) -> None:
        self.start = start if isinstance(start, Point) else Point(start[0], start[1])
        if end is not None and not isinstance(end, Point):
            end = Point(end[0], end[1])
        self.end = end
        self.angle = angle

    def propangle(self) -> float:
        """Return the wall angle."""

        return self.angle

    @classmethod
    def createarc(
        cls, start: Point, deltax: float, totalangle: float, numsegments: int
    ) -> tuple[list["Wall"], float]:
        """Approximate an arc with ``numsegments`` straight segments."""

        deltaangle = totalangle / numsegments
        segments = [cls(start, 0)]
        for i in range(numsegments):
            nextpoint = Shock.findintersection(
                segments[i].start,
                Point(start.x + deltax * (i + 1), start.y),
                deltaangle * i,
                89.9,
            )
            segments[i].end = nextpoint
            nextsegment = cls(nextpoint, deltaangle * (i + 1))
            segments.append(nextsegment)
        return segments, start.x + deltax * (numsegments + 1)

    def exists(self, x: float) -> bool:
        """Return ``True`` if ``x`` lies between ``start`` and ``end`` (if defined)."""

        beforestart = x < self.start.x
        afterend = False
        if self.end is not None:
            afterend = x > self.end.x
        return not beforestart and not afterend

    def getyposition(self, xposition: float) -> float:
        """Return the y coordinate on the wall at ``xposition`` or ``-inf``."""

        if self.exists(xposition):
            slope = math.tan(math.radians(self.angle))
            return (xposition - self.start.x) * slope + self.start.y
        return -float("inf")

    def __str__(self) -> str:  # pragma: no cover - simple display
        parts = [
            "Wall(",
            f"Start: {self.start}",
            f"Angle: {self.angle}",
        ]
        if self.end is not None:
            parts.append(f"End: {self.end}")
        return ", ".join(parts) + ")"
