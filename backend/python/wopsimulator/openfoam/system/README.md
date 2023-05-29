# Web of Phyngs Simulator OpenFOAM System Interface

## Folder Structure

- [blockmesh.py](blockmesh.py) - Provides the `blockMeshDict` file interface for creating the geometrical meshes
- [controldict.py](controldict.py) - Provides the `controlDict` file interface for setting up the OpenFOAM simulatior options
- [decomposepar.py](decomposepar.py) - Provides the `decomposeParDict` file interface for setting up the decomposition domains for multiprocessing
- [snappyhexmesh.py](snappyhexmesh.py) - Provides the `snappyHexMeshDict` file interface for snapping custom geometrical objects (e.g., custom STL files) on the mesh
