import math as m

import helperfuncs as h
from Point import Point


class Shock:
    def __init__(self, start, turningangle, gamma, upstreamv, upstreamtheta, end=None):
        if type(start) == Point:
            self.start = start
        elif type(start) == tuple or type(start) == list:
            self.start = Point(start[0], start[1])
        self.turningangle = turningangle
        self.v = upstreamv
        self.theta = upstreamtheta
        self.gamma = gamma
        self.angle = self.propangle()
        self.end = end

    def propangle(self):
        return h.shockprop(self.gamma, self.v, self.theta, self.turningangle)

    @staticmethod
    def findintersection(start1, start2, angle1, angle2):
        slope1 = m.tan(m.radians(angle1))
        slope2 = m.tan(m.radians(angle2))
        deltaslope = slope1 - slope2
        startx = max(start1.x, start2.x)
        line1 = lambda x: (x - start1.x) * slope1 + start1.y
        line2 = lambda x: (x - start2.x) * slope2 + start2.y
        ydif = line1(startx) - line2(startx)
        if deltaslope != 0:
            deltax = ydif / -deltaslope
        else:
            return None
        intersectionx = deltax + startx
        intersectiony = line1(intersectionx) / 2 + line2(intersectionx) / 2
        return Point(intersectionx, intersectiony)

    def findshockintersection(self, shock2):
        angle1 = self.propangle()
        angle2 = shock2.propangle()
        return self.findintersection(self.start, shock2.start, angle1, angle2)

    def getupstreamvals(self):
        return [self.v, self.theta, self.gamma]

    def getdownstreamvals(self):
        return [self.v + abs(self.turningangle), self.theta + self.turningangle, self.gamma]

    def __str__(self):
        return "\nStart: " + str(self.start) + "\nAngle: " + str(self.propangle())