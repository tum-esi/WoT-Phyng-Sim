# Web of Phyngs Simulator OpenFOAM Boundaries Interface

## Folder Structure

- [b_types/](b_types) - Contains OpenFOAM boundary dataclass types for setting up the boundary value types
- [boundary_conditions.py](boundary_conditions.py) - Provides an OpenFOAM boundary conditions parser and manipulator as well as boundary conditions mapping factory (e.g. to produce an instance with class BoundaryConditionT from "T" file aka temperature boundary conditions)
- [boundary_types.py](boundary_types.py) - Provides the boundary value mappings and boundary factory to automatically determine the boundary value type on class instantiation
