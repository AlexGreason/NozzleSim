import math as m
from copy import copy

import pygame

import helperfuncs as h


class Mesh:

    def __init__(self, gamma, initialmach, wallsegments, initialshocks, endexpansion, x=0):
        #  restrict to symmetric nozzles?
        #  Nah, it doesn't save a ton of effort and it would make duct simulation needlessly hard to retrofit
        #  so first, figure out how to simulate interacting shocks in free space, then it should be a fairly minor modification to add walls
        self.gamma = gamma
        # currently constant, but wouldn't be hard to make a function of mach, and if I can get temperature as a function
        # of mach I can do that too
        self.initialmach = initialmach
        self.wallsegments = wallsegments
        self.shocks = copy(initialshocks)
        # shocks contains all shocks that exist or have existed, and all wall segments in expansion section and as they are created
        self.activeshocks = copy(initialshocks)
        # activeshocks contains all shocks that still exist, and all wall segments in expansion section and as they are created
        # it checks to see, before tagging something as a pair, whether the intersection occurs in a location where that wall
        # actually exists, so shocks should never interact with nonexistent walls and I can just dump the whole expansion
        # section in there right at the start, then make up the compression section as I go.
        self.x = x
        self.endexpansion = endexpansion
        # x coordinate at which the expansion section ends. Controls whether shocks reflect off walls or cause them to
        # bend inwards

    # Alright, here's what the main loop looks like
    # 1. set up initial set of shocks, wall segments (will need to add something to deal with adding new wall segments during expansion section)
    # alright, so what I do is, I have all the wall segments in by default, but I don't include them when sorting, but I do include them when
    # finding the first intersection, by looking for if the "endpoint" field is defined and including that in the list of x locations if so.
    # that'll let me jump to the start of a new predefined wall section if it's the next event, and then I can spawn a region and expansion wave appropriately
    # 2. start at x value 0
    # 3. sort shocks/walls by current y value
    # 4. find pairs of neighboring lines where there's a type 1 on top and a type 2 on bottom, these will intersect
    # 5. calculate intersections for each of these pairs, select the one with the smallest x value
    # 6. go to that x value, spawn/destroy elements as needed to deal with that intersection
    # 7. go to step 3

    def simulate(self):
        pass

    def sortshocks(self, startx):
        xpositions = [x.start.x for x in self.activeshocks]
        slopes = [m.tan(m.radians(x.angle)) for x in self.activeshocks]
        ypositions = []
        for i in range(len(self.activeshocks)):
            ypositions += [(startx - xpositions[i]) * slopes[i] + self.activeshocks[i].start.y]

        shocks = list(zip(self.activeshocks, ypositions))
        shocks.sort(key=lambda x: x[1], reverse=True)
        print(shocks)
        return [x[0] for x in shocks], startx

    @staticmethod
    def exists(shock, x):
        beforestart = x < shock.start.x
        afterend = False
        try:
            afterend = x > shock.end.x
        except:
            pass
        return not beforestart and not afterend


    def findpairs(self, shocks, startx):
        pairs = []
        for i in range(len(shocks) - 1):
            interpoint = Shock.findintersection(shocks[i].start, shocks[i+1].start, shocks[i].angle, shocks[i+1].angle)
            if interpoint.x > startx and self.exists(shocks[i], interpoint.x)and self.exists(shocks[i+1], interpoint.x):
                pairs.append((shocks[i], shocks[i+1], interpoint))
        return pairs

    def firstintersection(self, shocks, startx):
        pairs = self.findpairs(shocks, startx)
        pairs.sort(key=lambda x: x[2].x)
        return pairs[0]

    # four cases:
    # 1. two shocks interfere in mid air
    # 2. shock reflects off wall
    # 3. shock hits wall, wall bends inward
    # 4. wall bends outward, shock is generated
    # Case four is the one that would benefit from the "region" structure, since I don't have an existing shock to piggyback off of
    # Hmm. what if I went back in a line along the wall and then going outwards, would I always hit the most recent shock?
    # Yes, because I would hit either the previous wall expansion and associated shock, or x=0, which I'll handle separately
    # So that gets me the shock from which I can extract the new values from calcregionparams
    # and that gets me the information I need to know to generate the new shock

    def handleintersection(self, object1, object2, x, y):
        if isinstance(object1, Shock) and isinstance(object2, Shock):
            newshocks =  self.newshocks(object1, object2, x, y)
            self.shocks += newshocks
            self.activeshocks += newshocks
            self.activeshocks.remove(object1)
            self.activeshocks.remove(object2)
            intersection = Point(x, y)
            object1.end = intersection
            object2.end = intersection
            self.x = x
        if ((isinstance(object1, Shock) and isinstance(object2, Wall)) or (
            isinstance(object1, Wall) and isinstance(object2, Shock))) and x < self.endexpansion:
            return ["reflect", None] # Method for handling expansion wave reflection, returns single new shock
        if ((isinstance(object1, Shock) and isinstance(object2, Wall)) or (
            isinstance(object1, Wall) and isinstance(object2, Shock))) and x > self.endexpansion:
            return ["absorb", None]  # Method for handling compression section generation, returns new wall segment
        if isinstance(object1, Wall) and isinstance(object2, Wall):
            raise TypeError('Both objects are walls. Your air got stuck.')
            # Actually, this case depends on whether or not I'm using handleintersection to manage the creation of
            # new shocks at corners in the expansion section or if I'm handling that separately.

    def getupstreamvalues(self, wallseg):
        start = wallseg.start
        if start.x == 0:
            return [h.calcv(self.gamma, 1, self.initialmach), 0, self.gamma]
        else:
            for x in self.shocks:
                if x.start == start and x != wallseg:
                    return x.getvals()

    def genwallshock(self, wall1, wall2):
        params = self.getupstreamvalues(wall2)
        turningangle = abs(wall2.angle - wall1.angle)
        return Shock(wall2.start, turningangle, params[2], params[0], params[1])

    def reflectshock(self, shock, x, y):
        bottomregion = Mesh.calcregionparams(shock.theta, shock.v, shock.gamma, shock)
        bottomshock = Shock(Point(x, y), -shock.turningangle, bottomregion[2], bottomregion[1], bottomregion[0])
        return bottomshock


    @staticmethod
    def calcregionparams(theta, v, gamma, shock):
        newgamma = gamma #update later if needed
        newtheta = theta + shock.turningangle
        newv = v + abs(shock.turningangle)
        return [newtheta, newv, newgamma]

    @staticmethod
    def newshocks(shock1, shock2, x, y):
        # this function takes two shockwaves that intersect at a point and determines the parameters of the shocks
        # after interacting with each other
        # the two shocks should have the same v, theta, and gamma because they share an upstream region, if
        # they are the next two shocks to intersect
        topregion = Mesh.calcregionparams(shock1.theta, shock1.v, shock1.gamma, shock1)
        bottomregion = Mesh.calcregionparams(shock2.theta, shock2.v, shock2.gamma, shock2)
        startpoint = Point(x, y)
        topshock = Shock(startpoint, shock2.turningangle, topregion[2], topregion[1], topregion[0])
        bottomshock = Shock(startpoint, shock1.turningangle, bottomregion[2], bottomregion[1], bottomregion[0])
        return [topshock, bottomshock]

    def drawallshocks(self, screen, displaybounds, screenx, screeny):
        for x in self.shocks:
            drawshock(screen, displaybounds, x, screenx, screeny)

    def printallshocks(self):
        for x in self.shocks:
            print(x)


class Point:

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distance(self, point2):
        return m.sqrt((self.x - point2.x) ** 2 + (self.y - point2.y) ** 2)

    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"

class Wall:


    def __init__(self, start, angle, end=None):
        self.start = start
        self.angle = angle
        self.end = end

    def propangle(self):
        return self.angle


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
        deltax = ydif / -deltaslope
        intersectionx = deltax + startx
        intersectiony = line1(intersectionx) / 2 + line2(intersectionx) / 2
        return Point(intersectionx, intersectiony)

    def findshockintersection(self, shock2):
        angle1 = self.propangle()
        angle2 = shock2.propangle()
        return self.findintersection(self.start, shock2.start, angle1, angle2)

    def getupstreamvals(self):
        return [self.v, self.theta, self.gamma]

    def __str__(self):
        return "\nStart: " + str(self.start) + "\nAngle: " + str(self.propangle())



class Region:
    def __init__(self, gamma, v, theta, corners, edges):
        self.gamma = gamma
        self.v = v
        self.theta = theta
        self.corners = corners
        self.edges = edges

def convertpoint(displaybounds, pointx, pointy, screenx, screeny):
    #note: in pygame coordinates, (0,0) is the top left. In nozzle coordinates, (minx, miny) is bottom left
    deltax = pointx - displaybounds[0][0]
    xrange = displaybounds[1][0] - displaybounds[0][0]
    propdiffx = deltax / xrange
    newx = propdiffx * screenx
    deltay = pointy - displaybounds[0][1]
    yrange = displaybounds[1][1] - displaybounds[0][1]
    propdiffy = deltay / yrange
    newy = screeny - propdiffy * screeny  # to adjust for difference in coordinate systems
    return newx, newy

def drawline(screen, displaybounds, start, angle, endx, screenx, screeny):
    endx = min(displaybounds[1][0], endx)
    slope = m.tan(m.radians(angle))
    deltax = endx - start.x
    endy = start.y + deltax * slope
    if endy > displaybounds[1][1]:
        end = Shock.findintersection(Point(0, displaybounds[1][1]), start, 0, angle)
    elif endy < displaybounds[0][1]:
        end = Shock.findintersection(Point(0, displaybounds[0][1]), start, 0, angle)
    else:
        end = Point(endx, endy)
    screenstart = convertpoint(displaybounds, start.x, start.y, screenx, screeny)
    screenend = convertpoint(displaybounds, end.x, end.y, screenx, screeny)
    pygame.draw.line(screen, (0, 0, 0), screenstart, screenend)
    pygame.display.update()

def drawshock(screen, displaybounds, shock, screenx, screeny):
    if shock.end is None:
        end = 1000
    else:
        end = shock.end.x
    angle = shock.propangle()
    drawline(screen, displaybounds, shock.start, angle, end, screenx, screeny)



if __name__ == "__main__":
    pygame.init()
    x_dim, y_dim = 600, 600
    screen = pygame.display.set_mode((x_dim, y_dim))
    screen.fill((255, 255, 255))
    displaybounds = [(0, -2), (4, 2)]
    shocka = Shock((0, 1), 10, 1.25, 0, 0)
    shockb = Shock((0, -1), -10, 1.25, 0, 0)
    mesh = Mesh(1.25, 1, [], [shocka, shockb], 2)
    shockc, shockd, intersection = mesh.firstintersection(mesh.activeshocks, mesh.x)
    mesh.handleintersection(shockc, shockd, intersection.x, intersection.y)
    mesh.drawallshocks(screen, displaybounds, 600, 600)
    mesh.printallshocks()
    running = True
    while running:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                running = False
                pygame.display.quit()
