# NozzleSim
Uses the method of characteristics to simulate supersonic flow in an axisymmetric nozzle, and use Busemann's method to construct a nozzle producing isentropic flow according to certain parameters

## Reference case verification

The script `reference_cases.py` prints a few simple characteristic angles and
compares them with values computed by hand using textbook formulas.  Each case
computes the propagation angle for a single expansion (bend) and shows the
difference between the analytical result and the value returned by the code.
Run it with `python3 reference_cases.py`.
