from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class Point:
    """Simple container for a two dimensional point."""

    x: float
    y: float

    def distance(self, point2: "Point") -> float:
        """Return the Euclidean distance to ``point2``."""

        return math.hypot(self.x - point2.x, self.y - point2.y)

    def equals(self, point2: "Point") -> bool:
        """Return ``True`` if ``point2`` has identical coordinates."""

        return self.x == point2.x and self.y == point2.y

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"({self.x}, {self.y})"
