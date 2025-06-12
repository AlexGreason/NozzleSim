import math as m
from functools import lru_cache




def sign(x):
    """Return the sign of *x* as ``1`` or ``-1``."""
    return m.copysign(1, x)

def machangle(mach):
    return m.asin(1/mach)

@lru_cache(maxsize=None)
def calcv(gamma, mach1, mach2):
    k = m.sqrt((gamma + 1)/(gamma - 1))  # dunno what actual significance of this is
    alpha1 = machangle(mach1)  # first mach angle
    alpha2 = machangle(mach2)  # second mach angle
    v1 = k * m.atan(1/(m.tan(alpha1) * k)) - (m.radians(90) - alpha1)  # first expansion angle
    v2 = k * m.atan(1/(m.tan(alpha2) * k)) - (m.radians(90) - alpha2)  # second expansion angle
    return m.degrees(v2 - v1)  # additional degrees of expansion needed to go from mach1 to mach2


def binarysearch(lowerbound, upperbound, target, steps, func):
    # note: only applies to monotonically increasing functions
    val = (upperbound + lowerbound)/2
    for i in range(steps):
        if func(val) > target:
            upperbound = val
            val = (upperbound + lowerbound) / 2
        if func(val) < target:
            lowerbound = val
            val = (upperbound + lowerbound) / 2
        if func(val) == target:
            return val
    return val

#  calcmach has been verified against the table, at least for gamma of 1.4
@lru_cache(maxsize=None)
def calcmach(gamma, mach1, angle, steps=30):
    if angle == 0:
        return 1

    def f(mach2):
        return calcv(gamma, mach1, mach2)

    return binarysearch(1, 100, angle, steps, f)


@lru_cache(maxsize=None)
def calcshockemitangle(gamma, angle, mach1=-1.0, v1=-1.0):
    if mach1 == -1:
        mach1 = calcmach(gamma, 1, v1)
    mach2 = calcmach(gamma, mach1, abs(angle))
    alpha1 = m.degrees(machangle( mach1))  # first mach angle
    alpha2 = m.degrees(machangle( mach2))  # second mach angle
    abar = (alpha1 + alpha2)/2
    return abar + .5 * abs(angle)


@lru_cache(maxsize=None)
def calcvmax(gamma):
    k = m.sqrt((gamma + 1) / (gamma - 1))
    return m.degrees(m.pi/2 * (k - 1))


@lru_cache(maxsize=None)
def calcshockpropangle(gamma, v1, theta, turningangle):
    mach1 = calcmach(gamma, 1, v1)
    mach2 = calcmach(gamma, 1, v1 + abs(turningangle))
    alpha1 = m.degrees(machangle( mach1))  # first mach angle
    alpha2 = m.degrees(machangle( mach2))  # second mach angle
    abar = -sign(turningangle) * (alpha1 + alpha2) / 2
    return abar + theta - turningangle/2


@lru_cache(maxsize=None)
def alphadiff(gamma, v1, v2):
    mach1 = calcmach(gamma, 1, v1)
    mach2 = calcmach(gamma, 1, v2)
    alpha1 = m.degrees(machangle( mach1))  # first mach angle
    alpha2 = m.degrees(machangle( mach2))  # second mach angle
    return alpha1 - alpha2


@lru_cache(maxsize=None)
def calcarearatio(gamma, mach):
    return 1/mach * ((2 + (gamma - 1) * mach ** 2)/(gamma + 1)) ** (.5 * ((gamma + 1)/(gamma - 1)))

@lru_cache(maxsize=None)
def calcmachfromarearatio(gamma, ratio, steps=20):

    def f(mach):
        return calcarearatio(gamma, mach)

    return binarysearch(1.1, 1000, ratio, steps, f)

@lru_cache(maxsize=None)
def shockangle(gamma, v, theta, turningangle):
    mach1 = calcmach(gamma, 1, v)
    alpha1 = m.degrees(machangle(mach1))
    return -sign(turningangle) * alpha1 + theta

@lru_cache(maxsize=None)
def shockprop(gamma, v, theta, turningangle):
    angle1 = shockangle(gamma, v, theta, turningangle)
    angle2 = shockangle(gamma, v + abs(turningangle), theta + turningangle, turningangle)
    return (angle1 + angle2)/2

#  GAMMAS
#  air: 1.4
#  rocket exhaust: 1.25 is a pretty good guess


if __name__ == "__main__":
    print(calcv(1.25, 1, 5))
    #  should differ by 8.1 degrees, because one is measuring from the x axis and one is measuring from the (post-turn) wall
    #  return the same value
    #  probably why I had that problem



# Desired Mach  Resulting Mach  desired expansion angle   resulting exp angle
# 5             9.6             72.82                      134
# 2             2.72

#Next up: a cone, or
