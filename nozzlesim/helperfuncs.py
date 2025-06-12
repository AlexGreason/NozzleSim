"""Utility math functions used throughout :mod:`nozzlesim`."""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Callable


def sign(x: float) -> float:
    """Return ``1`` for non-negative ``x`` and ``-1`` otherwise."""

    return 1.0 if x >= 0 else -1.0


def machangle(mach: float) -> float:
    """Return the Mach angle in radians for ``mach``."""

    return math.asin(1 / mach)


@lru_cache(maxsize=None)
def calcv(gamma: float, mach1: float, mach2: float) -> float:
    """Return the Prandtl-Meyer angle change from ``mach1`` to ``mach2``."""

    k = math.sqrt((gamma + 1) / (gamma - 1))
    alpha1 = machangle(mach1)
    alpha2 = machangle(mach2)
    v1 = k * math.atan(1 / (math.tan(alpha1) * k)) - (math.pi / 2 - alpha1)
    v2 = k * math.atan(1 / (math.tan(alpha2) * k)) - (math.pi / 2 - alpha2)
    return math.degrees(v2 - v1)


def binarysearch(
    lowerbound: float,
    upperbound: float,
    target: float,
    steps: int,
    func: Callable[[float], float],
) -> float:
    """Binary search for a monotonic ``func`` so ``func(x)`` approaches ``target``."""

    val = (upperbound + lowerbound) / 2
    for _ in range(steps):
        fval = func(val)
        if fval > target:
            upperbound = val
            val = (upperbound + lowerbound) / 2
        if func(val) < target:
            lowerbound = val
            val = (upperbound + lowerbound) / 2
        if func(val) == target:
            return val
    return val


@lru_cache(maxsize=None)
def calcmach(gamma: float, mach1: float, angle: float, steps: int = 30) -> float:
    """Return Mach number corresponding to ``angle`` increase from ``mach1``."""

    if angle == 0:
        return 1.0

    def f(mach2: float) -> float:
        return calcv(gamma, mach1, mach2)

    return binarysearch(1.0, 100.0, angle, steps, f)


@lru_cache(maxsize=None)
def calcshockemitangle(
    gamma: float, angle: float, mach1: float = -1.0, v1: float = -1.0
) -> float:
    """Return the emission angle of a shock after a wall turn."""

    if mach1 == -1:
        mach1 = calcmach(gamma, 1.0, v1)
    mach2 = calcmach(gamma, mach1, abs(angle))
    alpha1 = math.degrees(machangle(mach1))
    alpha2 = math.degrees(machangle(mach2))
    abar = (alpha1 + alpha2) / 2
    return abar + 0.5 * abs(angle)


@lru_cache(maxsize=None)
def calcvmax(gamma: float) -> float:
    """Return the maximum Prandtl-Meyer angle for ``gamma``."""

    k = math.sqrt((gamma + 1) / (gamma - 1))
    return math.degrees(math.pi / 2 * (k - 1))


@lru_cache(maxsize=None)
def calcshockpropangle(
    gamma: float, v1: float, theta: float, turningangle: float
) -> float:
    """Return propagation angle of a characteristic after a bend."""

    mach1 = calcmach(gamma, 1.0, v1)
    mach2 = calcmach(gamma, 1.0, v1 + abs(turningangle))
    alpha1 = math.degrees(machangle(mach1))
    alpha2 = math.degrees(machangle(mach2))
    abar = -sign(turningangle) * (alpha1 + alpha2) / 2
    return abar + theta - turningangle / 2


@lru_cache(maxsize=None)
def alphadiff(gamma: float, v1: float, v2: float) -> float:
    """Return difference in Mach angles corresponding to ``v1`` and ``v2``."""

    mach1 = calcmach(gamma, 1.0, v1)
    mach2 = calcmach(gamma, 1.0, v2)
    alpha1 = math.degrees(machangle(mach1))
    alpha2 = math.degrees(machangle(mach2))
    return alpha1 - alpha2


@lru_cache(maxsize=None)
def calcarearatio(gamma: float, mach: float) -> float:
    """Return area ratio ``A/A*`` for a given ``mach`` and ``gamma``."""

    return (
        1
        / mach
        * ((2 + (gamma - 1) * mach**2) / (gamma + 1))
        ** (0.5 * ((gamma + 1) / (gamma - 1)))
    )


@lru_cache(maxsize=None)
def calcmachfromarearatio(gamma: float, ratio: float, steps: int = 20) -> float:
    """Inverse of :func:`calcarearatio` using a binary search."""

    def f(mach: float) -> float:
        return calcarearatio(gamma, mach)

    return binarysearch(1.1, 1000.0, ratio, steps, f)


@lru_cache(maxsize=None)
def shockangle(gamma: float, v: float, theta: float, turningangle: float) -> float:
    """Return angle of the upstream characteristic at a wall turn."""

    mach1 = calcmach(gamma, 1.0, v)
    alpha1 = math.degrees(machangle(mach1))
    return -sign(turningangle) * alpha1 + theta


@lru_cache(maxsize=None)
def shockprop(gamma: float, v: float, theta: float, turningangle: float) -> float:
    """Return propagation angle of a characteristic through a wall turn."""

    angle1 = shockangle(gamma, v, theta, turningangle)
    angle2 = shockangle(
        gamma, v + abs(turningangle), theta + turningangle, turningangle
    )
    return (angle1 + angle2) / 2
