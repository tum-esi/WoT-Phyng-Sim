# Backend Implementation

The backend is split into 2+1 parts:

- [Python backend](python) where the simulation is excecuted along with a Flask interface to it
- [NodeJS backend](nodejs) where the Web of Things Scripting API is, which communicates to the python simulation server
- [ParaView backend](paraview), which allows to access the simulation results
