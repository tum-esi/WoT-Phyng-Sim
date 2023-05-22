"""Coupled boundaries type dataclasses"""
from dataclasses import dataclass
from typing import List

from .general_boundaries import Mixed


@dataclass
class CyclicAMI:
    neighbourPatch: str = None
    transform: str = None


@dataclass
class Cyclic:
    neighbourPatch: str = None
    transform: str = None


@dataclass
class Fan:
    pass


@dataclass
class CompressibleTurbulentTemperatureCoupledBaffleMixed(Mixed):
    neighbourFieldName: str = None
    kappaMethod: str = None
    kappa: str = None
    Tnbr: str = None
    value: str = None
    value_uniform: bool = None
    thicknessLayers: List[float] = None
    kappaLayers: List[float] = None
    alphaAni: float = None
