import math as m
from copy import copy

import pygame

import helperfuncs as h
from Point import Point
from Shock import Shock
from Wall import Wall

epsilon = 10 ** -10


class Mesh:
    def __init__(self, gamma, initialmach, wallsegments, initialshocks, endexpansion, x=0):
        #  restrict to symmetric nozzles?
        #  Nah, it doesn't save a ton of effort and it would make duct simulation needlessly hard to retrofit
        #  so first, figure out how to simulate interacting shocks in free space, then it should be a fairly
        #  minor modification to add walls
        self.gamma = gamma
        # currently constant, but wouldn't be hard to make a function of mach,
        # and if I can get temperature as a function of mach I can do that too
        self.initialmach = initialmach
        self.wallsegments = wallsegments
        self.shocks = copy(initialshocks)
        # shocks contains all shocks that exist or have existed
        # and all wall segments in expansion section and as they are created
        self.activeshocks = copy(initialshocks)
        # activeshocks contains all shocks that still exist
        # and all wall segments in expansion section and as they are created
        # it checks to see, before tagging something as a pair, whether the intersection occurs in a location
        # where that wall actually exists, so shocks should never interact with nonexistent walls
        # and I can just dump the whole expansion section in there right at the start
        # then make up the compression section as I go.
        self.x = x
        self.endexpansion = endexpansion
        # x coordinate at which the expansion section ends. Controls whether shocks reflect off walls or cause them to
        # bend inwards

    # Alright, here's what the main loop looks like
    # 1. set up initial set of shocks, wall segments (will need to add something to deal with adding new wall segments
    # during expansion section) alright, so what I do is, I have all the wall segments in by default, but I don't
    # include them when sorting, but I do include them when finding the first intersection,
    # by looking for if the "endpoint" field is defined and including that in the list of x locations if so. that'll
    # let me jump to the start of a new predefined wall section if it's the next event, and then I can spawn a region
    # and expansion wave appropriately
    # 2. start at x value 0
    # 3. sort shocks/walls by current y value
    # 4. find pairs of neighboring lines where there's a type 1 on top and a type 2 on bottom, these will intersect
    # 5. calculate intersections for each of these pairs, select the one with the smallest x value
    # 6. go to that x value, spawn/destroy elements as needed to deal with that intersection
    # 7. go to step 3

    def simulate(self):
        event = self.firstevent(self.activeshocks, self.x)
        while event is not None and self.x < 3:
            self.handleevent(event)
            event = self.firstevent(self.activeshocks, self.x)

    @staticmethod
    def sortshocks(shocks, startx):
        xpositions = [x.start.x for x in shocks]
        slopes = [m.tan(m.radians(x.angle)) for x in shocks]
        ypositions = []
        for i in range(len(shocks)):
            ypositions += [(startx + epsilon - xpositions[i]) * slopes[i] + shocks[i].start.y]
        shocks = list(zip(shocks, ypositions))
        shocks.sort(key=lambda x: x[1], reverse=True)
        print(shocks)
        return [x[0] for x in shocks]

    def handled(self, shocks, object1, object2, x, y):
        intersection = Point(x, y)
        if isinstance(object1, Shock) and isinstance(object2, Shock):
            for x in shocks:
                if x.start.equals(intersection) and isinstance(x, Shock):
                    return True
            return False
        if (isinstance(object1, Shock) and isinstance(object2, Wall)) or (
                    isinstance(object1, Wall) and isinstance(object2, Shock)) and x <= self.endexpansion:
            for x in shocks:
                if x.start.equals(intersection) and isinstance(x, Shock):
                    return True
            return False
        if (isinstance(object1, Shock) and isinstance(object2, Wall)) or (
                    isinstance(object1, Wall) and isinstance(object2, Shock)) and x > self.endexpansion:
            for x in shocks:
                if x.start.equals(intersection) and isinstance(x, Wall):
                    return True
            return False

    def findpairs(self, shocks, startx):
        pairs = []
        shocks = self.sortshocks(shocks, startx)
        for i in range(len(shocks) - 1):
            interpoint = Shock.findintersection(shocks[i].start, shocks[i + 1].start, shocks[i].angle,
                                                shocks[i + 1].angle)
            if interpoint is not None:
                if interpoint.x >= startx and shocks[i].exists(interpoint.x - epsilon) and \
                        shocks[i + 1].exists(interpoint.x - epsilon) and not self.handled(shocks, shocks[i],
                                                                                          shocks[i + 1], interpoint.x,
                                                                                          interpoint.y):
                    pairs.append((shocks[i], shocks[i + 1], interpoint))
        return pairs

    def firstintersection(self, shocks, startx):
        pairs = self.findpairs(shocks, startx)
        pairs.sort(key=lambda x: x[2].x)
        if len(pairs) > 0:
            return pairs[0]
        return None

    @staticmethod
    def removeended(shocks, endx):
        notended = []
        for x in shocks:
            try:
                ended = x.end.x < endx
            except AttributeError:
                ended = False
            if not ended:
                notended.append(x)
        return notended

    def firstevent(self, shocks, startx):
        shocks = self.removeended(shocks, startx)
        intersection = self.firstintersection(shocks, startx)
        if intersection is not None:
            if not (isinstance(intersection[0], Wall) and isinstance(intersection[1], Wall)):
                intersectionx = intersection[2].x
            else:
                intersectionx = float("inf")
        else:
            intersectionx = float("inf")
        firstwallend = float("inf")
        wall = None
        nextwall = None
        for x in shocks:
            if type(x) == Wall and x.end is not None:
                shock = None
                next = None
                for y in self.shocks:
                    if y.start.equals(x.end) and isinstance(y, Shock):
                        shock = y
                    if y.start.equals(x.end) and isinstance(y, Wall):
                        next = y
                if firstwallend > x.end.x >= startx:
                    if shock is None:
                        firstwallend = x.end.x
                        wall = x
                        nextwall = next
        if firstwallend <= intersectionx and nextwall is not None:
            return ["wall", [wall, nextwall, wall.end]]
        if intersection is not None:
            return ["intersection", intersection]
        return None

    # four cases:
    # 1. two shocks interfere in mid air
    # 2. shock reflects off wall
    # 3. shock hits wall, wall bends inward
    # 4. wall bends outward, shock is generated
    # Case four is the one that would benefit from the "region" structure, since I don't have an existing shock
    # to piggyback off of Hmm. what if I went back in a line along the wall and then going outwards, would I always
    # hit the most recent shock? Yes, because I would hit either the previous wall expansion and associated shock,
    # or x=0, which I'll handle separately So that gets me the shock from which I can extract the new values from
    # calcregionparams and that gets me the information I need to know to generate the new shock

    def handleintersection(self, object1, object2, x, y):
        if isinstance(object1, Shock) and isinstance(object2, Shock):
            newshocks = Shock.newshocks(object1, object2, x, y)
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
            if isinstance(object1, Shock):
                shock = object1
            else:
                shock = object2
            newshock = self.reflectshock(shock, x,
                                         y)  # Method for handling expansion wave reflection, returns single new shock
            self.activeshocks.remove(shock)
            shock.end = newshock.start
            self.activeshocks.append(newshock)
            self.shocks.append(newshock)
            self.x = x
        if ((isinstance(object1, Shock) and isinstance(object2, Wall)) or (
                    isinstance(object1, Wall) and isinstance(object2, Shock))) and x > self.endexpansion:
            return ["absorb", None]  # Method for handling compression section generation, returns new wall segment
        if isinstance(object1, Wall) and isinstance(object2, Wall):
            raise TypeError('Both objects are walls. Your air got stuck.')
            # Actually, this case depends on whether or not I'm using handleintersection to manage the creation of
            # new shocks at corners in the expansion section or if I'm handling that separately.

    def handleevent(self, event):
        if event[0] == "wall":
            newshock = self.genwallshock(event[1][0], event[1][1])
            self.activeshocks.append(newshock)
            self.shocks.append(newshock)
            self.x = event[1][2].x
        if event[0] == "intersection":
            self.handleintersection(event[1][0], event[1][1], event[1][2].x, event[1][2].y)

    def getupstreamvalues(self, wallseg):
        start = wallseg.start
        if start.x == 0:
            return [h.calcv(self.gamma, 1, self.initialmach), 0, self.gamma]
        else:
            for x in self.shocks:
                if x.start == start and x != wallseg:
                    return x.getdownsrteamvals()

    def genwallshock(self, wall1, wall2):
        params = self.getupstreamvalues(wall1)
        turningangle = wall2.angle - wall1.angle
        return Shock(wall2.start, turningangle, params[2], params[0], params[1])

    @staticmethod
    def reflectshock(shock, x, y):
        bottomregion = Shock.calcregionparams(shock.theta, shock.v, shock.gamma, shock)
        bottomshock = Shock(Point(x, y), -shock.turningangle, bottomregion[2], bottomregion[1], bottomregion[0])
        return bottomshock

    def drawallshocks(self, screen, displaybounds, screenx, screeny):
        for x in self.shocks:
            drawshock(screen, displaybounds, x, screenx, screeny)

    def printallshocks(self):
        for x in self.shocks:
            print(x)


def convertpoint(displaybounds, pointx, pointy, screenx, screeny):
    # note: in pygame coordinates, (0,0) is the top left. In nozzle coordinates, (minx, miny) is bottom left
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
        end = displaybounds[1][0] + 1  # go to the edge of the screen
    else:
        end = shock.end.x
    angle = shock.propangle()
    drawline(screen, displaybounds, shock.start, angle, end, screenx, screeny)


if __name__ == "__main__":
    pygame.init()
    x_dim, y_dim = 600, 600
    screen = pygame.display.set_mode((x_dim, y_dim))
    screen.fill((255, 255, 255))
    displaybounds = [(0, -4), (8, 4)]
    walla = Wall((0, 1), 0, (1, 1))
    wallb = Wall((1, 1), 10)
    wallc = Wall((0, -1), 0, (1, -1))
    walld = Wall((1, -1), -10)
    mesh = Mesh(1.25, 1, [], [walla, wallb, wallc, walld], 100)
    mesh.simulate()
    mesh.drawallshocks(screen, displaybounds, 600, 600)
    mesh.printallshocks()
    running = True
    while running:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                running = False
                pygame.display.quit()
