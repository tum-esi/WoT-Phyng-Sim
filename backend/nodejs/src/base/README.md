# Web of Phyngs Simulator NodeJS Base Implementations

## Folder Structure

- [actuator.ts](actuator.ts) - Provides an abstract Actuator Thing class that can be extended further to implement the actual thing (e.g., heater)
- [axios-request.ts](axios-request.ts) - Provides an extension/modification of a conventionak axios library
- [case.ts](case.ts) - Provides an abstract Case Thing class that can be extended further to implement the actual case thing (e.g., CHT Case)
- [helpers.ts](helpers.ts) - Provides functions that are commonly used in other files for the code simplification
- [interfaces.ts](interfaces.ts) - Provides the interfaces and types used by the other classes
- [phyng.ts](phyng.ts) - Provides an abstract Phyng class that can be extended further to implement the actual Phyng (e.g., heater or sensor)
- [properties.ts](properties.ts) - Provides abstract behavior/property classes that can be combined with Actuators to further implement the actual thing (e.g., heater)
- [schemas.ts](schemas.ts) - Provides helpers to merge the PDs and CDs schemas and a function for schema validations
- [sensor.ts](sensor.ts) - Provides an abstract Sensor Thing class that can be extended further to implement the actual thing (e.g., temperature sensor)
- [simulator.ts](simulator.ts) - Provides a Simulator Thing class
- [thing.ts](thing.ts) - Provides an abstract Thing class that can be extended further to implement the actual thing (e.g., actuator or case). It allows its children to produce WoT Things from Thing Models
