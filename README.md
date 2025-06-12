# NozzleSim
Uses the method of characteristics to simulate supersonic flow in an axisymmetric nozzle, and use Busemann's method to construct a nozzle producing isentropic flow according to certain parameters

## Reference case verification

Reference cases validating characteristic propagation angles are included in the
test suite.  Run ``pytest`` to execute them.

## Running Tests

Install required dependencies and run the test suite with coverage:

```bash
pip install -r requirements.txt
pytest
```

## Code style

This project uses [Black](https://black.readthedocs.io/) for formatting. Run
``black .`` before committing changes.
