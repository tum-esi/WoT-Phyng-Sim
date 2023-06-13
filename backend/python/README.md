# Web of Phyngs Simulator Python Backend

This folder contains the code WoP Simulator Python Backend.

All the WoP used cases are stored here and are defined in
the `wop-config.json` as follows:

```json
{
  "my_room": {
    "type": "cht",
    "path": "./my_room"
  }
}
```

The error texts and traces are then stored in the file `errors.json` as follows:

```json
{
  "texts" : [],
  "traces": []
}
```

## Folder Structure

- [server_resources/](server_resources) - Provides the Flask RESTful API scripts 
- [wopsimulator/](wopsimulator) - Provides the OpenFOAM python interface
- [Dockerfile](Dockerfile) - Docker image commands file
- [paraview_server.py](paraview_server.py) - An interface for connecting to ParaView server
- [server.ini](server.ini) - Provides Flask server configuration files
- [server.py](server.py) - Flask server entrypoint
- [workaround.py](workaround.py) - A workaround for PyFoam to disable particular errors
