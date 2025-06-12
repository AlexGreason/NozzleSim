import math as m

from Point import Point
from Shock import Shock


class Wall:
    def __init__(self, start, angle, end=None):
        if type(start) == Point:
            self.start = start
        elif type(start) == tuple or type(start) == list:
            self.start = Point(start[0], start[1])
        if end is not None:
            if type(end) == Point:
                self.end = end
            elif type(end) == tuple or type(end) == list:
                self.end = Point(end[0], end[1])
        else:
            self.end = end
        self.angle = angle

    def propangle(self):
        return self.angle

    @classmethod
    def createarc(cls, start, deltax, totalangle, numsegments):
        deltaangle = totalangle/numsegments
        segments = [cls(start, 0)]
        for i in range(numsegments):
            nextpoint = Shock.findintersection(segments[i].start, Point(start.x + deltax * (i+1), start.y), deltaangle * i, 89.9)
            segments[i].end = nextpoint
            nextsegment = cls(nextpoint, deltaangle * (i + 1))
            segments.append(nextsegment)
        return segments, start.x + deltax * (numsegments + 1)

    def exists(self, x):
        beforestart = x < self.start.x
        afterend = False
        try:
            afterend = x > self.end.x
        except AttributeError:
            pass
        return not beforestart and not afterend

    def getyposition(self, xposition):
        if(self.exists(xposition)):
            slope = m.tan(m.radians(self.angle))
            return (xposition - self.start.x) * slope + self.start.y
        return -float("inf")

