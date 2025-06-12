import nozzlesim.mesh as mesh_module


class DummyMesh(mesh_module.Mesh):
    def __init__(self):
        # initialize with dummy values for parent
        super().__init__(1.4, 1.0, [], [], 0, 1)
        self.events = ["e1", "e2", "e3"]
        self.counter = 0

    def firstevent(self, shocks, startx):
        return self.events.pop(0) if self.events else None

    def handleevent(self, event):
        self.counter += 1
        if self.counter == 2:
            self.remainingangle = 0


def test_simulate_stops_when_remainingangle_zero():
    m = DummyMesh()
    m.simulate()
    assert m.counter == 2
