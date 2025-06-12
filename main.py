import numpy as np
import pygame

from nozzlesim import Wall, Point, Mesh

if __name__ == "__main__":
    pygame.init()
    x_dim, y_dim = 800, 800
    screen = pygame.display.set_mode((x_dim, y_dim))
    screen.fill((255, 255, 255))
    displaybounds = [(0, -10), (20, 10)]
    n = 20
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