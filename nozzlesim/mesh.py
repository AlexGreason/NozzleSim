"""Basic nozzle mesh utilities."""

from copy import copy
import math as m

import numpy as np
import pygame

from . import helperfuncs as h
from .point import Point
from .shock import Shock
from .wall import Wall

epsilon = 10**-10


class Mesh:
    """Container for tracking walls and shocks during a nozzle simulation."""

    def __init__(
        self,
        gamma,
        initialmach,
        wallsegments,
        initialshocks,
        endexpansion,
        remainingangle,
        x=0,
    ):
        """Create a new mesh.

        Parameters
        ----------
        gamma : float
            Specific heat ratio of the gas.
        initialmach : float
            Mach number at the inlet.
        wallsegments : list[Wall]
            Static wall segments already present in the domain.
        initialshocks : list[Shock | Wall]
            Shocks and walls that already exist at ``x``.
        endexpansion : float
            Location where the expansion section ends.
        remainingangle : float
            Angle remaining in the wall turn when the mesh is created.
        x : float, optional
            Starting ``x`` location.
        """

        self.gamma = gamma
        self.initialmach = initialmach
        self.wallsegments = wallsegments

        # ``shocks`` keeps every shock or wall created during the simulation.
        self.shocks = copy(initialshocks)

        # ``activeshocks`` only contains objects that still exist at ``x``.
        self.activeshocks = copy(initialshocks)

        # Simulation state
        self.x = x
        self.endexpansion = endexpansion
        self.remainingangle = remainingangle

    # Alright, here's what the main loop looks like
    # 1. set up initial set of shocks, wall segments (will need to add something to deal with adding new wall segments
    # during expansion section) alright, so what I do is, I have all the wall segments in by default, but I don't
    # include them when sorting, but I do include them when finding the first intersection,
    # by looking for if the "endpoint" field is defined and including that in the list of x locations if so. that'll
    # let me jump to the start of a new predefined wall section if it's the next event, and then I can spawn an
    # expansion wave appropriately
    # 2. start at x value 0
    # 3. sort shocks/walls by current y value
    # 4. find pairs of neighboring lines where there's a type 1 on top and a type 2 on bottom, these will intersect
    # 5. calculate intersections for each of these pairs, select the one with the smallest x value
    # 6. go to that x value, spawn/destroy elements as needed to deal with that intersection
    # 7. go to step 3

    def simulate(self, stop=float("inf")):
        """Propagate the mesh until no more events occur or ``stop`` is reached."""

        event = self.firstevent(self.activeshocks, self.x)
        lastcheck = self.remainingangle <= 0

        while event is not None and self.x < stop:
            self.handleevent(event)
            event = self.firstevent(self.activeshocks, self.x)
            if lastcheck:
                return

    @staticmethod
    def sortshocks(shocks, startx):
        """Return *shocks* sorted by their projected y value at ``startx``."""

        def proj_y(seg):
            slope = m.tan(m.radians(seg.angle))
            return (startx + epsilon - seg.start.x) * slope + seg.start.y

        return sorted(shocks, key=proj_y, reverse=True)

    def handled(self, shocks, object1, object2, x, y):
        if isinstance(object1, Shock) and isinstance(object2, Shock):
            cls = Shock
        elif isinstance(object1, Wall) ^ isinstance(object2, Wall):
            cls = Shock if x <= self.endexpansion else Wall
        else:
            return False

        for seg in shocks:
            if seg.start.x == x and seg.start.y == y and isinstance(seg, cls):
                return True

        return False

    def findpairs(self, shocks, startx):
        pairs = []
        sorted_shocks = self.sortshocks(shocks, startx)

        for top, bottom in zip(sorted_shocks, sorted_shocks[1:]):
            interpoint = Shock.findintersection(
                top.start, bottom.start, top.angle, bottom.angle
            )
            if interpoint is None:
                continue

            checkx1 = interpoint.x - epsilon
            checkx2 = interpoint.x - epsilon
            if checkx1 < top.start.x:
                checkx1 = interpoint.x
            if checkx2 < bottom.start.x:
                checkx2 = interpoint.x

            if (
                interpoint.x >= startx
                and top.exists(checkx1)
                and bottom.exists(checkx2)
                and not self.handled(shocks, top, bottom, interpoint.x, interpoint.y)
            ):
                pairs.append((top, bottom, interpoint))

        return pairs

    def firstintersection(self, shocks, startx):
        pairs = self.findpairs(shocks, startx)
        return min(pairs, key=lambda x: x[2].x) if pairs else None

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

        intersectionx = float("inf")
        if intersection and not (
            isinstance(intersection[0], Wall) and isinstance(intersection[1], Wall)
        ):
            intersectionx = intersection[2].x

        firstwallend = float("inf")
        wall = nextwall = None

        for seg in shocks:
            if isinstance(seg, Wall) and seg.end is not None:
                shock = None
                nxt = None
                for candidate in self.shocks:
                    if candidate.start.equals(seg.end):
                        if isinstance(candidate, Shock):
                            shock = candidate
                        elif isinstance(candidate, Wall):
                            nxt = candidate
                if firstwallend > seg.end.x >= startx and shock is None:
                    firstwallend = seg.end.x
                    wall = seg
                    nextwall = nxt

        if firstwallend <= intersectionx and nextwall is not None:
            return ["wall", [wall, nextwall, wall.end]]
        if intersection and intersectionx != float("inf"):
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

        elif (isinstance(object1, Shock) and isinstance(object2, Wall)) or (
            isinstance(object1, Wall) and isinstance(object2, Shock)
        ):
            if x < self.endexpansion:
                shock = object1 if isinstance(object1, Shock) else object2
                newshock = self.reflectshock(shock, x, y)
                self.activeshocks.remove(shock)
                shock.end = newshock.start
                self.activeshocks.append(newshock)
                self.shocks.append(newshock)
            else:
                shock = object1 if isinstance(object1, Shock) else object2
                wall = object2 if shock is object1 else object1
                newwall = self.contract(wall, shock, x, y)
                self.activeshocks.remove(wall)
                self.activeshocks.remove(shock)
                self.shocks.append(newwall)
                self.activeshocks.append(newwall)
            self.x = x

        else:
            raise TypeError("Both objects are walls. Your air got stuck.")
            # Actually, this case depends on whether or not I'm using handleintersection
            # to manage the creation of new shocks at corners in the expansion section
            # or if I'm handling that separately.

    def contract(self, wall, shock, x, y):
        point = Point(x, y)
        wall.end = point
        shock.end = point
        newwall = Wall(point, wall.angle + shock.turningangle)
        self.remainingangle = abs(wall.angle + shock.turningangle)
        return newwall

    def handleevent(self, event):
        if event[0] == "wall":
            newshock = self.genwallshock(event[1][0], event[1][1])
            self.activeshocks.append(newshock)
            self.shocks.append(newshock)
            self.x = event[1][2].x
        elif event[0] == "intersection":
            self.handleintersection(
                event[1][0], event[1][1], event[1][2].x, event[1][2].y
            )

    def getupstreamvalues(self, wallseg):
        """Return ``[v, theta, gamma]`` upstream of ``wallseg``."""

        start = wallseg.start
        if start.x == 0:
            return [h.calcv(self.gamma, 1, self.initialmach), 0, self.gamma]

        for x in self.shocks:
            if x.start == start and x != wallseg:
                return x.getdownstreamvals()

    def genwallshock(self, wall1, wall2):
        """Create a shock generated by a turn from ``wall1`` to ``wall2``."""

        params = self.getupstreamvalues(wall1)
        turningangle = wall2.angle - wall1.angle
        return Shock(wall2.start, turningangle, params[2], params[0], params[1])

    @staticmethod
    def reflectshock(shock, x, y):
        """Return a reflected shock at ``x, y`` from ``shock``."""

        bottomregion = Shock.calcregionparams(shock.theta, shock.v, shock.gamma, shock)
        bottomshock = Shock(
            Point(x, y),
            -shock.turningangle,
            bottomregion[2],
            bottomregion[1],
            bottomregion[0],
        )
        return bottomshock

    def drawallshocks(self, screen, displaybounds, screenx, screeny, justwalls=False):
        """Draw all shocks and walls to a ``pygame`` ``screen``."""

        for seg in self.shocks:
            if isinstance(seg, Wall) or not justwalls:
                drawshock(screen, displaybounds, seg, screenx, screeny)

    def printallshocks(self):
        for x in self.shocks:
            print(x)

    def calcarearatio(self):
        """Return the square of the vertical distance between top and bottom walls."""

        maxy = -float("inf")
        miny = float("inf")
        for seg in self.shocks:
            if isinstance(seg, Wall):
                if seg.start.y > maxy:
                    maxy = seg.start.y
                if seg.start.y < miny:
                    miny = seg.start.y
        diff = maxy - miny
        return diff**2

    def getxytable(self, startx, numpoints, deltax):
        """Return a list of ``(x, y)`` wall positions."""

        table = []
        for i in range(numpoints):
            maxy = -float("inf")
            for seg in self.shocks:
                if isinstance(seg, Wall):
                    ypos = seg.getyposition(startx + deltax * i)
                    if ypos > maxy:
                        maxy = ypos
            table.append((startx + deltax * i, maxy))
        return table


def convertpoint(displaybounds, pointx, pointy, screenx, screeny):
    """Convert physical ``(pointx, pointy)`` to screen coordinates."""

    # In pygame (0, 0) is the top left. In nozzle coordinates (minx, miny) is
    # the bottom left.  This helper converts between the two.
    deltax = pointx - displaybounds[0][0]
    xrange = displaybounds[1][0] - displaybounds[0][0]
    propdiffx = deltax / xrange
    newx = propdiffx * screenx

    deltay = pointy - displaybounds[0][1]
    yrange = displaybounds[1][1] - displaybounds[0][1]
    propdiffy = deltay / yrange
    newy = screeny - propdiffy * screeny

    return newx, newy


def drawline(screen, displaybounds, start, angle, endx, screenx, screeny):
    """Draw a line segment representing a shock or wall."""

    endx = min(displaybounds[1][0], endx)
    slope = m.tan(m.radians(angle))
    deltax = endx - start.x
    endy = start.y + deltax * slope
    end = None
    if endy > displaybounds[1][1]:
        end = Shock.findintersection(Point(0, displaybounds[1][1]), start, 0, angle)
    elif endy < displaybounds[0][1]:
        end = Shock.findintersection(Point(0, displaybounds[0][1]), start, 0, angle)
    if end is None:
        end = Point(endx, endy)

    screenstart = convertpoint(displaybounds, start.x, start.y, screenx, screeny)
    screenend = convertpoint(displaybounds, end.x, end.y, screenx, screeny)
    if 0 < screenstart[0] < screenx and 0 < screenstart[1] < screeny:
        pygame.draw.line(screen, (0, 0, 0), screenstart, screenend)
        pygame.display.update()


def drawshock(screen, displaybounds, shock, screenx, screeny):
    """Draw ``shock`` to ``screen`` within ``displaybounds``."""

    end = displaybounds[1][0] + 1 if shock.end is None else shock.end.x
    angle = shock.propangle()
    drawline(screen, displaybounds, shock.start, angle, end, screenx, screeny)


if __name__ == "__main__":
    pygame.init()
    x_dim, y_dim = 800, 800
    screen = pygame.display.set_mode((x_dim, y_dim))
    screen.fill((255, 255, 255))
    displaybounds = [(0, -10), (20, 10)]
    n = 45
    theta = 34.45
    topwalls, endx = Wall.createarc(Point(0, 0.5), 0.007, theta, n)
    bottomwalls, endx = Wall.createarc(Point(0, -0.5), 0.007, -theta, n)
    print(endx)
    mesh = Mesh(1.25, 1, [], topwalls + bottomwalls, endx, 1)
    mesh.simulate()
    table = mesh.getxytable(0, 1000, 0.011)
    mesh.drawallshocks(screen, displaybounds, x_dim, y_dim)
    np.savetxt("table.csv", table, delimiter=",")
    print(mesh.calcarearatio())
    running = True
    while running:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                running = False
                pygame.display.quit()
