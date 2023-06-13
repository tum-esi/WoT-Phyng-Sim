# Web of Phyngs Simulator

## Folder Structure

- [geometry/](geometry) - Contains Gmsh geometry creation interface implementations
- [openfoam/](openfoam) - Contains OpenFOAM interface implementations
- [phyngs/](phyngs) - Contains Phyngs implementations
- [case_base.py](case_base.py) - Provides an OpenFOAM base simulation case implementation
- [cht_case.py](cht_case.py) - Provides a CHT OpenFOAM simulation case implementation
- [exceptions.py](exceptions.py) - Provides a list of custom simulation exceptions
- [loader.py](loader.py) - Provides functions for listing, creating, loading, saving and deleting the simulation cases
- [runtime_monitor.py](runtime_monitor.py) - Provides a program that monitors the simulator to ensure the "real-time"-like beheavior by observing the simulation time and real time, and stoping the case for eliminating the difference
- [variables.py](variables.py) - Provides common simulation variables
