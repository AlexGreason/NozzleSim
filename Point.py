import math as m

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distance(self, point2):
        return m.sqrt((self.x - point2.x) ** 2 + (self.y - point2.y) ** 2)

    def equals(self, point2):
        return self.x == point2.x and self.y == point2.y

    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"
