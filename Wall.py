from Point import Point

class Wall:
    def __init__(self, start, angle, end=None):
        if type(start) == Point:
            self.start = start
        elif type(start) == tuple or type(start) == list:
            self.start = Point(start[0], start[1])
        if not end is None:
            if type(end) == Point:
                self.end = end
            elif type(end) == tuple or type(end) == list:
                self.end = Point(end[0], end[1])
        else:
            self.end = end
        self.angle = angle

    def propangle(self):
        return self.angle

    def exists(self, x):
        beforestart = x < self.start.x
        afterend = False
        try:
            afterend = x > self.end.x
        except AttributeError:
            pass
        return not beforestart and not afterend